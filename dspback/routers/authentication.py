import json

from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Request
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import HTMLResponse, RedirectResponse, Response

from dspback.config import Settings, get_settings, oauth
from dspback.database.models import UserTable
from dspback.database.procedures import delete_access_token
from dspback.dependencies import create_or_update_user, get_current_user, get_db, url_for
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
async def logout(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: UserTable = Depends(get_current_user),
):
    response = RedirectResponse(url="/")
    response.delete_cookie("Authorization", domain=settings.outside_host)
    delete_access_token(db, user)
    return response


@router.get('/health', status_code=status.HTTP_200_OK)
async def perform_health_check(db: Session = Depends(get_db)):
    output = 'database is ok'
    try:
        db.execute('SELECT 1')
    except Exception as e:
        output = str(e)

    return {"db": output}
