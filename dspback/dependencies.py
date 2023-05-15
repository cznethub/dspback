from typing import Any

from beanie.odm.operators.update.general import Set
from fastapi import Request, Security

from dspback.authentication.fastapi_resource_server import JwtDecodeOptions, OidcResourceServer, GrantType
from dspback.config import get_settings
from dspback.pydantic_schemas import User


decode_options = JwtDecodeOptions(verify_aud=False)

auth_scheme = OidcResourceServer(
    "https://auth.cuahsi.io/realms/HydroShare",
    jwt_decode_options=decode_options,
    allowed_grant_types=[GrantType.IMPLICIT]
)


async def create_or_update_user(preferred_username: str) -> User:
    await User.find_one(User.preferred_username == preferred_username)\
        .upsert(Set({'preferred_username': preferred_username}), on_insert=User(preferred_username=preferred_username))
    return await User.find_one(User.preferred_username == preferred_username)

async def get_current_user(claims: dict = Security(auth_scheme)) -> User:
    user = await create_or_update_user(claims["preferred_username"])
    return user
