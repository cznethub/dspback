import time
import typing

from fastapi import FastAPI, Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.config import Config
from starlette.responses import HTMLResponse, RedirectResponse, JSONResponse
from db import db

from authlib.integrations.starlette_client import OAuth, OAuthError

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

config = Config('/app/config/.env')
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
    url_path = app.router.url_path_for(name, **path_params)
    # TOOD - get the parent router path instead of hardcoding /api
    return "http://{}/api{}".format(outside_host, url_path)

def _access_token(request: Request, repository: str):
    orcid = request.session.get('orcid')
    expires_at = db[orcid][repository]['expires_at']
    if expires_at < time.time():
        pass
    return db[orcid][repository]['access_token']


@app.route('/')
def home(request: Request):
    orcid = request.session.get('orcid')
    if orcid:
        if orcid in db:
            return JSONResponse(content={orcid: db[orcid]})
        return JSONResponse(content={"status": f"{orcid} not recognized"})
    return JSONResponse(content={"status": "Not logged in"})


@app.route('/login')
async def login(request: Request):
    redirect_uri = _url_for('auth')
    if 'X-Forwarded-Proto' in request.headers:
        redirect_uri = redirect_uri.replace('http:', request.headers['X-Forwarded-Proto'] + ':')
    return await oauth.orcid.authorize_redirect(request, redirect_uri)


@app.route('/logout')
async def logout(request: Request):
    request.session.pop('orcid', None)
    return RedirectResponse(url='/')


@app.get('/authorize/{repository}')
async def authorize_repository(repository: str, request: Request):
    orcid = request.session.get('orcid')
    if not orcid:
        return RedirectResponse("/login")
    redirect_uri = _url_for('auth_repository', repository=repository)
    return await getattr(oauth, repository).authorize_redirect(request, redirect_uri)


@app.route('/auth')
async def auth(request: Request):
    try:
        token = await oauth.orcid.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    if token['orcid'] in db:
        db[token['orcid']]['name'] = token['name']
        db[token['orcid']]['access_token'] = token['access_token']
    else:
        db[token['orcid']] = {"name": token['name'], 'access_token': token['access_token']}
    request.session['orcid'] = token['orcid']
    return RedirectResponse(url='/api')


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
    db[orcid][repository] = token
    return RedirectResponse(url='/api')
