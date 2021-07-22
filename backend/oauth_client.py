import time
import typing

from fastapi import Request, HTTPException, APIRouter
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from starlette.config import Config
from starlette.responses import HTMLResponse, RedirectResponse, JSONResponse

from authlib.integrations.starlette_client import OAuth, OAuthError

from backend import fastapi_users
from backend.database import database, RepositoryCreate
from backend.database import User

from httpx_oauth.oauth2 import OAuth2


app = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

config = Config('config/.env')


orcid_client = OAuth2(
    config.get('ORCID_CLIENT_ID'),
    config.get('ORCID_CLIENT_SECRET'),
    "https://sandbox.orcid.org/oauth/authorize",
    "https://sandbox.orcid.org/oauth/token",
    #refresh_token_endpoint="https://sandbox.orcid.org/oauth/refresh",
    revoke_token_endpoint="https://sandbox.orcid.org/oauth/revoke",
)

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
    return "http://{}/api{}".format(outside_host, url_path)

def _access_token(request: Request, repository: str):
    orcid = request.session.get('orcid')
    expires_at = database[orcid][repository]['expires_at']
    if expires_at < time.time():
        pass
    return database[orcid][repository]['access_token']


@app.get('/')
def home(user: User = Depends(fastapi_users.current_user())):
    return JSONResponse(content={"status": f"Logged in as {user.email}"})


@app.get('/authorize/{repository}')
async def authorize_repository(repository: str, request: Request, user: User = Depends(fastapi_users.current_user())):
    redirect_uri = _url_for('auth_repository', repository=repository)
    return await getattr(oauth, repository).authorize_redirect(request, redirect_uri)


@app.get("/auth/{repository}")
async def auth_repository(request: Request, repository: str):
    try:
        repo = getattr(oauth, repository)
        token = await repo.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    orcid = request.session.get('orcid')
    if not orcid:
        raise HTTPException(status_code=400, detail="No logged in with an orcid, cannot authorize hydroshare")

    repo = RepositoryCreate(type=str(token['name']).upper(), access_token=token['access_token'])
    return RedirectResponse(url='/api')
