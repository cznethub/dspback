import typing

from datetime import timedelta, datetime, time
from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session, subqueryload
from starlette import status
from starlette.status import HTTP_403_FORBIDDEN

from dspback.config import outside_host, JWT_SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from dspback.models import TokenData, Repo
from dspback.database.models import UserTable, RepositoryTable


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
    return "https://{}{}".format(outside_host, url_path)


def access_token(user: UserTable, repo_type: Repo):
    repository = next(filter(lambda repo: repo.type == repo_type, user.repositories), None)
    if not repository:
        return None
    # TODO - setup configuration for extra tiem
    if repository.expires_at and repository.expires_at < time.time():
        # TODO - refresh_token and update the repository row
        pass
    return repository.access_token


def create_access_token(data: dict, minutes: typing.Optional[timedelta] = None):
    to_encode = data.copy()
    if minutes:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + access_token_expires
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_user(db: Session, orcid_response):
    db_user = UserTable(name=orcid_response['name'], orcid=orcid_response['orcid'],
                        access_token=orcid_response['access_token'], refresh_token=orcid_response['refresh_token'],
                        expires_in=orcid_response['expires_in'], expires_at=orcid_response['expires_at'])
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, db_user: UserTable, orcid_response):
    db_user.access_token = orcid_response['access_token']
    db_user.refresh_token = orcid_response['refresh_token']
    db_user.expires_in = orcid_response['expires_in']
    db_user.expires_at = orcid_response['expires_at']
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_repository(repository: str, db: Session, user: UserTable, repository_response):
    # zenodo does not have a refresh_token apparently
    db_repository = RepositoryTable(type=repository, access_token=repository_response['access_token'],
                                    repo_user_id='blah', user_id=user.id)
    db.add(db_repository)
    db.commit()
    db.refresh(db_repository)
    return db_repository


def update_repository(db: Session, db_repository: RepositoryTable, repository_response):
    db_repository.access_token = repository_response['access_token']
    # db_repository.refresh_token = repository_response['refresh_token']
    db.add(db_repository)
    db.commit()
    db.refresh(db_repository)
    return db_repository


def get_user(db: Session, orcid: str):
    return db.query(UserTable).filter(UserTable.orcid == orcid).options(subqueryload('repositories')).first()


def get_repository(db: Session, user: UserTable, repository: str):
    return db.query(RepositoryTable).filter(RepositoryTable.user_id == user.id, RepositoryTable.type == repository).first()


def get_db(request: Request):
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
