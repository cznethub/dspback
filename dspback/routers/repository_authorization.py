from fastapi import Request, APIRouter, status, HTTPException
from fastapi.params import Depends
from starlette.responses import HTMLResponse, RedirectResponse, JSONResponse

from sqlalchemy.orm import Session

from authlib.integrations.starlette_client import OAuthError

from dspback.config import oauth
from dspback.dependencies import get_current_user, url_for, get_db, get_repository, update_repository, \
    create_repository, access_token
from dspback.models import User

router = APIRouter()


@router.get('/authorize/{repository}')
async def authorize_repository(repository: str, request: Request, user: User = Depends(get_current_user)):
    redirect_uri = url_for(request, 'auth_repository', repository=repository)
    return await getattr(oauth, repository).authorize_redirect(request, redirect_uri)


@router.get("/auth/{repository}")
async def auth_repository(request: Request, repository: str, user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    try:
        repo = getattr(oauth, repository)
        token = await repo.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')

    db_repository: User = get_repository(db, user, repository)
    if db_repository:
        update_repository(db, db_repository, token)
    else:
        create_repository(db, user, token)
    return RedirectResponse(url_for(request, "home"))


@router.get("/access_token/{repository}")
async def get_access_token(repository: str, user: User = Depends(get_current_user)):
    token = access_token(user, repository)
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse({"token": token})
