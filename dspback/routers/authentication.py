import json

from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, RedirectResponse, JSONResponse, Response

from dspback.config import oauth, Settings
from dspback.database.models import UserTable
from dspback.dependencies import create_access_token, create_or_update_user, get_current_user, get_db, url_for
from dspback.config import get_settings
from dspback.pydantic_schemas import ORCIDResponse, User

router = APIRouter()


@router.get('/', response_model=User)
def home(user: UserTable = Depends(get_current_user)):
    return User.from_orm(user)


@router.get('/login')
async def login(request: Request, window_close: bool = False, settings: Settings = Depends(get_settings)):
    redirect_uri = url_for(request, 'auth')
    if 'X-Forwarded-Proto' in request.headers:
        redirect_uri = redirect_uri.replace('http:', request.headers['X-Forwarded-Proto'] + ':')
    return await oauth.orcid.authorize_redirect(request, redirect_uri + f"?window_close={window_close}")


@router.get('/logout')
async def logout(settings: Settings = Depends(get_settings)):
    response = RedirectResponse(url="/")
    response.delete_cookie("Authorization", domain=settings.outside_host)
    return response


@router.get('/auth')
async def auth(request: Request, window_close: bool = False, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        orcid_response = await oauth.orcid.authorize_access_token(request)
        orcid_response = ORCIDResponse(**orcid_response)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    user: UserTable = create_or_update_user(db, orcid_response)

    access_token = create_access_token(data={"sub": user.orcid},
                                       expiration_minutes=settings.access_token_expire_minutes,
                                       secret_key=settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    token = jsonable_encoder(access_token)
    if window_close:
        responseHTML = '<html><head><title>CzHub Sign In</title></head><body></body><script>res = %value%; window.opener.postMessage(res, "*");window.close();</script></html>'
        responseHTML = responseHTML.replace(
          "%value%",
          json.dumps({
            'token': token,
            'expiresIn': orcid_response.expires_in
          })
        )
        return HTMLResponse(responseHTML)

    return Response(token)
