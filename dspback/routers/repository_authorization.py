import json
from datetime import datetime, timedelta

from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, JSONResponse

from dspback.config import Settings, get_settings, oauth, repository_config
from dspback.database.models import UserTable
from dspback.database.procedures import delete_repository_access_token
from dspback.dependencies import (
    create_or_update_repository_token,
    get_current_repository_token,
    get_current_user,
    get_db,
    url_for,
)
from dspback.pydantic_schemas import RepositoryToken, RepositoryType

router = APIRouter()


@router.get('/authorize/{repository}')
async def authorize_repository(repository: str, request: Request):
    redirect_uri = url_for(request, 'auth_repository', repository=repository)
    return await getattr(oauth, repository).authorize_redirect(request, redirect_uri)


@router.get("/auth/{repository}")
async def auth_repository(
    request: Request,
    repository: RepositoryType,
    user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        repo = getattr(oauth, repository)
        token = await repo.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')

    # TODO sort out await
    await create_or_update_repository_token(db, user, repository, token)
    responseHTML = '<html><head><title>CzHub Sign In</title></head><body></body><script>res = %value%; window.opener.postMessage(res, "*");window.close();</script></html>'
    responseHTML = responseHTML.replace("%value%", json.dumps({'token': token}))
    return HTMLResponse(responseHTML)


@router.get("/access_token/{repository}")
async def get_access_token(
    request: Request,
    repository: RepositoryType,
    user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    try:
        repository_token = await get_current_repository_token(request, repository, user, db, settings)
    except HTTPException as http_exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=http_exception.detail)
    return {"access_token": repository_token.access_token}


@router.delete("/access_token/{repository}")
async def delete_access_token(
    repository: RepositoryType, user: UserTable = Depends(get_current_user), db: Session = Depends(get_db)
):
    delete_repository_access_token(db, repository, user)


@router.get("/urls/{repository}")
async def get_urls(repository: RepositoryType, user: UserTable = Depends(get_current_user)):
    # TODO, build schema for repository config and validate
    if repository not in repository_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse(repository_config[repository])
