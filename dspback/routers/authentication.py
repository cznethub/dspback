from fastapi import Request, APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.params import Depends
from starlette.responses import HTMLResponse, RedirectResponse, JSONResponse

from sqlalchemy.orm import Session

from authlib.integrations.starlette_client import OAuthError

from backend.config import oauth
from backend.dependencies import get_current_user, url_for, get_user, update_user, create_user, create_access_token, \
    get_db
from backend.models import User

router = APIRouter()


@router.get('/')
def home(user: User = Depends(get_current_user)):
    reponse_dict = {"orcid": user.orcid, "orcid_access_token": user.access_token}
    for repo in user.repositories:
        reponse_dict[f"{repo.type}_access_token"] = repo.access_token
    return JSONResponse(content=reponse_dict)


@router.get('/login')
async def login(request: Request):
    redirect_uri = url_for(request, 'auth')
    if 'X-Forwarded-Proto' in request.headers:
        redirect_uri = redirect_uri.replace('http:', request.headers['X-Forwarded-Proto'] + ':')
    return await oauth.orcid.authorize_redirect(request, redirect_uri)


@router.get('/logout')
async def logout(request: Request):
    response = RedirectResponse(url=url_for(request, 'home'))
    response.delete_cookie("Authorization", domain="localhost")
    return response


@router.get('/auth')
async def auth(request: Request, db: Session = Depends(get_db)):
    try:
        orcid_response = await oauth.orcid.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    db_user: User = get_user(db, orcid_response['orcid'])
    if db_user:
        update_user(db, db_user, orcid_response)
    else:
        db_user = create_user(db, orcid_response)

    access_token = create_access_token(
        data={"sub": db_user.orcid}
    )

    token = jsonable_encoder(access_token)

    response = RedirectResponse(url=url_for(request, 'home'))
    response.set_cookie(
        "Authorization",
        f"Bearer {token}",
    )
    return response
