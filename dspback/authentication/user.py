from fastapi import Security

from dspback.authentication.fastapi_resource_server import JwtDecodeOptions, GrantType, OidcResourceServer
from dspback.database.procedures import create_or_update_user
from dspback.pydantic_schemas import User

decode_options = JwtDecodeOptions(verify_aud=False)

auth_scheme = OidcResourceServer(
    "https://auth.cuahsi.io/realms/HydroShare",
    jwt_decode_options=decode_options,
    allowed_grant_types=[GrantType.IMPLICIT]
)

async def get_current_user(claims: dict = Security(auth_scheme)) -> User:
    user = await create_or_update_user(claims["preferred_username"])
    return user