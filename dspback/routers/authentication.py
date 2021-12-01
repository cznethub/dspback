from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, RedirectResponse

from dspback.config import OUTSIDE_HOST, oauth
from dspback.database.models import UserTable
from dspback.dependencies import create_access_token, create_or_update_user, get_current_user, get_db, url_for
from dspback.schemas import ORCIDResponse, User

router = APIRouter()


@router.get('/', response_model=User)
def home(user: UserTable = Depends(get_current_user)):
    return User.from_orm(user)


@router.get('/login')
async def login(request: Request):
    redirect_uri = url_for(request, 'auth')
    if 'X-Forwarded-Proto' in request.headers:
        redirect_uri = redirect_uri.replace('http:', request.headers['X-Forwarded-Proto'] + ':')
    return await oauth.orcid.authorize_redirect(request, redirect_uri)


@router.get('/logout')
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("Authorization", domain=OUTSIDE_HOST)
    return response


@router.get('/auth')
async def auth(request: Request, db: Session = Depends(get_db)):
    try:
        orcid_response = await oauth.orcid.authorize_access_token(request)
        orcid_response = ORCIDResponse(**orcid_response)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    user: UserTable = create_or_update_user(db, orcid_response)

    access_token = create_access_token(data={"sub": user.orcid})

    token = jsonable_encoder(access_token)

    response = RedirectResponse(url="/")
    response.set_cookie("Authorization", f"Bearer {token}", domain=OUTSIDE_HOST, expires=orcid_response.expires_in)
    return response
