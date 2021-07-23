import typing
from datetime import timedelta, datetime

from fastapi import Request, HTTPException, APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.params import Depends
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from pydantic import BaseModel
from starlette import status
from starlette.config import Config
from starlette.responses import HTMLResponse, RedirectResponse, JSONResponse

from sqlalchemy.orm import Session

from jose import JWTError, jwt

from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.status import HTTP_403_FORBIDDEN

from backend.database import TokenData, ORCIDResponse, UserTable
from backend.database import User


app = APIRouter()

class OAuth2PasswordBearerCookie(OAuth2):
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

oauth2_scheme = OAuth2PasswordBearerCookie(tokenUrl="/token")

config = Config('config/.env')

oauth = OAuth(config)
oauth.register(name='hydroshare',
               authorize_url="https://www.hydroshare.org/o/authorize/",
               token_endpoint="https://www.hydroshare.org/o/token/")
oauth.register(name='orcid',
               authorize_url='https://sandbox.orcid.org/oauth/authorize',
               token_endpoint='https://sandbox.orcid.org/oauth/token',
               client_kwargs={'scope': 'openid'})
oauth.register(name='zenodo',
               authorize_url='https://sandbox.zenodo.org/oauth/authorize',
               client_kwargs={'scope': 'deposit:write deposit:actions', 'response_type': "code"},
               token_endpoint='https://sandbox.zenodo.org/oauth/token',
               access_token_params={'grant_type': 'client_credentials', 'scope': 'deposit:write deposit:actions',
                                    'client_id': config.get('ZENODO_CLIENT_ID'),
                                    'client_secret': config.get('ZENODO_CLIENT_SECRET')})

outside_host = "localhost"

def _url_for(name: str, **path_params: typing.Any) -> str:
    url_path = app.url_path_for(name, **path_params)
    # TOOD - get the parent router path instead of hardcoding /api
    return "https://{}/api{}".format(outside_host, url_path)

def _access_token(request: Request, repository: str):
    #orcid = request.session.get('orcid')
    #expires_at = database[orcid][repository]['expires_at']
    #if expires_at < time.time():
    #    pass
    #return database[orcid][repository]['access_token']
    return None

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict, expires_delta: typing.Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_user(db: Session, orcid_response):
    db_user = UserTable(name=orcid_response['name'], orcid=orcid_response['orcid'], access_token=orcid_response['access_token'], refresh_token=orcid_response['refresh_token'], expires_in=orcid_response['expires_in'], expires_at=orcid_response['expires_at'])
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_user: User, orcid_response: ORCIDResponse):
    db_user.access_token = orcid_response['access_token']
    db_user.refresh_token = orcid_response['refresh_token']
    db_user.expires_in = orcid_response['expires_in']
    db_user.expires_at = orcid_response['expires_at']
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, orcid: str):
    return db.query(UserTable).filter(UserTable.orcid == orcid).first()

def get_db(request: Request):
    return request.state.db

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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

@app.get('/')
def home(user: User = Depends(get_current_user)):
    return JSONResponse(content={"status": f"Logged in as {user.orcid}"})

@app.get('/login')
async def login(request: Request):
    redirect_uri = _url_for('auth')
    if 'X-Forwarded-Proto' in request.headers:
        redirect_uri = redirect_uri.replace('http:', request.headers['X-Forwarded-Proto'] + ':')
    return await oauth.orcid.authorize_redirect(request, redirect_uri)

@app.get('/logout')
async def logout():
    response = RedirectResponse(url=_url_for('home'))
    response.delete_cookie("Authorization", domain="localhost")
    return response

@app.get('/auth')
async def auth(request: Request, db: Session = Depends(get_db)):
    try:
        orcid_response = await oauth.orcid.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    db_user: User = get_user(db, orcid_response['orcid'])
    if db_user:
        update_user(db, db_user, orcid_response)
    else:
        create_user(db, orcid_response)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.orcid}, expires_delta=access_token_expires
    )

    token = jsonable_encoder(access_token)

    response = RedirectResponse(url=_url_for('home'))
    response.set_cookie(
        "Authorization",
        f"Bearer {token}",
    )
    return response

@app.get('/authorize/{repository}')
async def authorize_repository(repository: str, request: Request, user: User = Depends(get_current_user)):
    redirect_uri = _url_for('auth_repository', repository=repository)
    return await getattr(oauth, repository).authorize_redirect(request, redirect_uri)


@app.get("/auth/{repository}")
async def auth_repository(request: Request, repository: str, user: User = Depends(get_current_user)):
    try:
        repo = getattr(oauth, repository)
        token = await repo.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    orcid = request.session.get('orcid')
    if not orcid:
        raise HTTPException(status_code=400, detail="No logged in with an orcid, cannot authorize hydroshare")

    #repo = RepositoryCreate(type=str(token['name']).upper(), access_token=token['access_token'])
    return RedirectResponse(url='/api')
