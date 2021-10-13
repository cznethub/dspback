import typing

from datetime import timedelta, datetime
from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session, subqueryload
from starlette import status
from starlette.status import HTTP_403_FORBIDDEN

from dspback.config import OUTSIDE_HOST, JWT_SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, repository_config
from dspback.schemas import TokenData, RepositoryType, User, ORCIDResponse, RepositoryToken
from dspback.database.models import UserTable, RepositoryTokenTable


class OAuth2AuthorizationBearerToken(OAuth2):
    '''
    Handles a bearer Authorization token in both a header or a cookie, making it compatible with both web and API
    requests.
    '''

    def __init__(
            self,
            tokenUrl: str,
            scheme_name: str = None,
            scopes: dict = None,
            auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> typing.Optional[str]:
        header_authorization: str = request.headers.get("Authorization")
        cookie_authorization: str = request.cookies.get("Authorization")

        header_scheme, header_param = get_authorization_scheme_param(
            header_authorization
        )
        cookie_scheme, cookie_param = get_authorization_scheme_param(
            cookie_authorization
        )

        if header_scheme.lower() == "bearer":
            authorization = True
            scheme = header_scheme
            param = header_param

        elif cookie_scheme.lower() == "bearer":
            authorization = True
            scheme = cookie_scheme
            param = cookie_param

        else:
            authorization = False

        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None
        return param


class Token(BaseModel):
    access_token: str
    token_type: str


oauth2_scheme = OAuth2AuthorizationBearerToken(tokenUrl="/token")


def url_for(request: Request, name: str, **path_params: typing.Any) -> str:
    url_path = request.app.url_path_for(name, **path_params)
    # TODO - get the parent router path instead of hardcoding /api
    return "https://{}{}".format(OUTSIDE_HOST, url_path)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + access_token_expires
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_or_update_user(db: Session, orcid_response: ORCIDResponse):
    db_user: UserTable = get_user_table(db, orcid_response.orcid)
    if db_user:
        db_user = update_user_table(db, db_user, orcid_response)
    else:
        db_user = create_user_table(db, orcid_response)
    return User.from_orm(db_user)


def create_user_table(db: Session, orcid_response: ORCIDResponse):
    db_user = UserTable(name=orcid_response.name, orcid=orcid_response.orcid,
                        access_token=orcid_response.access_token, refresh_token=orcid_response.refresh_token,
                        expires_in=orcid_response.expires_in, expires_at=orcid_response.expires_at)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_table(db: Session, db_user: UserTable, orcid_response: ORCIDResponse):
    db_user.access_token = orcid_response.access_token
    db_user.refresh_token = orcid_response.refresh_token
    db_user.expires_in = orcid_response.expires_in
    db_user.expires_at = orcid_response.expires_at
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_or_update_repository_token(db, user, repository, token) -> RepositoryToken:
    repository_token_table: RepositoryTokenTable = get_repository_table(db, user, repository)
    if repository_token_table:
        repository_token_table = update_repository_token(db, repository_token_table, token)
    else:
        repository_token_table = create_repository_token(repository, db, user, token)
    return RepositoryToken.from_orm(repository_token_table)


def create_repository_token(repository: str, db: Session, user: User, repository_response) -> RepositoryTokenTable:
    # zenodo does not have a refresh_token apparently
    db_repository = RepositoryTokenTable(type=repository, access_token=repository_response['access_token'],
                                         repo_user_id='blah', user_id=user.id,
                                         # refresh_token=repository_response['access_token'],
                                         expires_in=repository_response['expires_in'],
                                         expires_at=repository_response['expires_at'])
    db.add(db_repository)
    db.commit()
    db.refresh(db_repository)
    return db_repository


def update_repository_token(db: Session, db_repository: RepositoryTokenTable, repository_response) -> RepositoryTokenTable:
    db_repository.access_token = repository_response['access_token']
    # db_repository.refresh_token = repository_response['refresh_token']
    db_repository.expires_in = repository_response['expires_in']
    db_repository.expires_at = repository_response['expires_at']
    # db_repository.refresh_token = repository_response['refresh_token']
    db.add(db_repository)
    db.commit()
    db.refresh(db_repository)
    return db_repository


def get_user_table(db: Session, orcid: str) -> UserTable:
    user_table = db.query(UserTable).filter(UserTable.orcid == orcid).options(subqueryload('repository_tokens')).first()
    return user_table


def get_user(db: Session, orcid: str) -> User:
    user_table = get_user_table(db, orcid)
    return User.from_orm(user_table)


def get_repository_table(db: Session, user: UserTable, repository_type: RepositoryType) -> RepositoryTokenTable:
    repository_table = db.query(RepositoryTokenTable).filter(RepositoryTokenTable.user_id == user.id,
                                                             RepositoryTokenTable.type == repository_type).first()
    return repository_table


def get_db(request: Request) -> Session:
    return request.state.db


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        orcid: str = payload.get("sub")
        if orcid is None:
            raise credentials_exception
        token_data = TokenData(orcid=orcid)
    except JWTError:
        raise credentials_exception
    user = get_user(db, orcid=token_data.orcid)
    if user is None:
        raise credentials_exception
    return user
