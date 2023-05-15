from http.client import HTTPException
from typing import Any, Optional

from authlib.integrations.starlette_client import OAuth
from beanie.odm.operators.update.general import Set
from fastapi import Request, Depends, Security

from dspback.authentication.fastapi_resource_server import JwtDecodeOptions, OidcResourceServer
from dspback.config import get_settings
from dspback.pydantic_schemas import User


def url_for(request: Request, name: str, **path_params: Any) -> str:
    url_path = request.app.url_path_for(name, **path_params)
    # TODO - get the parent router path instead of hardcoding /api
    return "https://{}{}".format(get_settings().outside_host, url_path)


decode_options = JwtDecodeOptions(verify_aud=False)

auth_scheme = OidcResourceServer(
    "https://auth.cuahsi.io/realms/HydroShare",
    scheme_name="Keycloak",
    jwt_decode_options=decode_options,
)


async def create_or_update_user(preferred_username: str) -> User:
    await User.find_one(User.preferred_username == preferred_username)\
        .upsert(Set({'preferred_username': preferred_username}), on_insert=User(preferred_username=preferred_username))
    return await User.find_one(User.preferred_username == preferred_username)

async def get_current_user(claims: dict = Security(auth_scheme)) -> User:
    user = await create_or_update_user(claims["preferred_username"])
    return user
