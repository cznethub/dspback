import json

import requests
from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Request
from fastapi.params import Depends
from motor.motor_asyncio import AsyncIOMotorCollection as Session
from starlette import status
from starlette.responses import HTMLResponse, RedirectResponse, Response

from dspback.config import Settings, get_settings, oauth
from dspback.dependencies import create_or_update_user, get_current_user, url_for
from dspback.pydantic_schemas import ORCIDResponse, User

router = APIRouter()


@router.get('/')
def home(user: User = Depends(get_current_user)):
    return f"{user.name} is logged in"


@router.get('/login')
async def login(request: Request, window_close: bool = False, settings: Settings = Depends(get_settings)):
    redirect_uri = url_for(request, 'auth')
    if 'X-Forwarded-Proto' in request.headers:
        redirect_uri = redirect_uri.replace('http:', request.headers['X-Forwarded-Proto'] + ':')
    response = await oauth.orcid.authorize_redirect(request, redirect_uri + f"?window_close={window_close}")
    return response


@router.get('/logout')
async def logout(
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_user),
):
    response = RedirectResponse(url="/")
    response.delete_cookie("Authorization", domain=settings.outside_host)
    user.access_token = None
    await user.save()
    return response


@router.get('/auth')
async def auth(request: Request, window_close: bool = False):
    try:
        orcid_response = await oauth.orcid.authorize_access_token(request)
        orcid_response = ORCIDResponse(**orcid_response)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    user: User = await create_or_update_user(orcid_response)
    token = user.access_token
    if window_close:
        responseHTML = '<html><head><title>CzHub Sign In</title></head><body></body><script>res = %value%; window.opener.postMessage(res, "*");window.close();</script></html>'
        responseHTML = responseHTML.replace(
            "%value%", json.dumps({'token': token, 'expiresIn': orcid_response.expires_in})
        )
        return HTMLResponse(responseHTML)

    return Response(token)


@router.get('/health', status_code=status.HTTP_200_OK)
async def perform_health_check(settings: Settings = Depends(get_settings)):
    db_health = False
    orcid_health = False
    hydroshare_health = False
    zenodo_health = False

    try:
        # db.execute('SELECT 1')
        # db_health = True
        pass
    except Exception as e:
        output = str(e)

    resp = requests.get(settings.orcid_health_url)
    if resp.status_code == 200:
        orcid_health = True

    resp = requests.get(settings.hydroshare_health_url)
    if resp.status_code == 200 and resp.text == "all good in the hood":
        hydroshare_health = True

    resp = requests.get(settings.zenodo_health_url)
    if resp.status_code == 200:
        zenodo_health = True

    return {"database": db_health, "orcid": orcid_health, "hydroshare": hydroshare_health, "zenodo": zenodo_health}
