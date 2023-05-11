import requests
from fastapi import APIRouter, Request
from fastapi.params import Depends
from starlette import status

from dspback.authentication.auth import get_oidc
from dspback.config import Settings, get_settings
from dspback.dependencies import get_current_user

router = APIRouter()

oidc = get_oidc()

@router.get('/')
@oidc.require_login
async def home(request: Request):
    return f"{request.user_info['preferred_username']} is logged in"

@router.get('/user')
@oidc.require_login
async def home_user(request: Request):
    user = await get_current_user(request)
    return f"{user.preferred_username} is logged in"

@router.get('/login')
@oidc.require_login
async def login(request: Request, get_user_info=True):
    return {"message": "success"}


@router.get('/logout')
async def logout(request: Request):
    return oidc.logout(request)


@router.get('/health', status_code=status.HTTP_200_OK)
async def perform_health_check(settings: Settings = Depends(get_settings)):
    db_health = False
    keycloak_health = False

    try:
        # db.execute('SELECT 1')
        # db_health = True
        pass
    except Exception as e:
        output = str(e)

    resp = requests.get(settings.keycloak_health_url)
    if resp.status_code == 200:
        keycloak_health = True

    return {"database": db_health, "keycloak": keycloak_health}
