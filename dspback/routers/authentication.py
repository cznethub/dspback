import requests
from fastapi import APIRouter, Request
from fastapi.params import Depends
from starlette import status

from dspback.config import Settings, get_settings
from dspback.dependencies import get_current_user
from dspback.pydantic_schemas import User

router = APIRouter()

@router.get('/')
async def home(request: Request):#, user: User = Depends(get_current_user)):
    return request.query_params.get("code")

@router.get('/user')
async def home_user(request: Request, user: User = Depends(get_current_user)):
    return f"{user.preferred_username} is logged in"

@router.get('/login')
async def login(request: Request, get_user_info=True):
    return {"message": "success"}


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
