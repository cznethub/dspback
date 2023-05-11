from datetime import datetime, timedelta
from typing import Any, Optional

from beanie.odm.operators.update.general import Set
from fastapi import Depends, HTTPException, Request
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt
from pydantic import BaseModel
from starlette import status
from starlette.status import HTTP_403_FORBIDDEN

from dspback.config import get_settings
from dspback.pydantic_schemas import KeycloakResponse, TokenData, User, KeycloakUserResponse


class OAuth2AuthorizationBearerToken(OAuth2):
    """
    Handles a bearer Authorization token in both a header or a cookie, making it compatible with both web and API
    requests.
    """

    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request, access_token: Optional[str] = None) -> Optional[str]:
        authorization = False
        scheme = "bearer"

        if access_token:
            authorization = True
            param = access_token

        else:
            header_authorization: str = request.headers.get("Authorization")
            cookie_authorization: str = request.cookies.get("Authorization")

            header_scheme, header_param = get_authorization_scheme_param(header_authorization)
            cookie_scheme, cookie_param = get_authorization_scheme_param(cookie_authorization)

            if header_scheme.lower() == scheme:
                authorization = True
                param = header_param

            elif cookie_scheme.lower() == scheme:
                authorization = True
                param = cookie_param

        if not authorization:
            if self.auto_error:
                raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Not authenticated")
            else:
                return None
        return param


class Token(BaseModel):
    access_token: str
    token_type: str


oauth2_scheme = OAuth2AuthorizationBearerToken(tokenUrl="/token")


def url_for(request: Request, name: str, **path_params: Any) -> str:
    url_path = request.app.url_path_for(name, **path_params)
    # TODO - get the parent router path instead of hardcoding /api
    return "https://{}{}".format(get_settings().outside_host, url_path)


def encode_access_token(orcid: str) -> str:
    data = {"sub": orcid}
    settings = get_settings()
    to_encode = data.copy()
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.utcnow() + access_token_expires
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def create_or_update_user(keycloak_response: KeycloakUserResponse) -> User:
    user_dict = {
        'name': keycloak_response.name,
        'keycloak_access_token': keycloak_response.access_token,
        'refresh_token': keycloak_response.refresh_token,
        'expires_in': keycloak_response.expires_in,
        'expires_at': keycloak_response.expires_at,
    }
    await User.find_one(User.orcid == keycloak_response.orcid).upsert(Set(user_dict), on_insert=User(**user_dict))
    user = await User.find_one(User.orcid == keycloak_response.orcid)
    return user


class TokenException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


async def get_user_from_token(token: str, settings) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        token_data = TokenData(**payload)
        if token_data.orcid is None:
            raise TokenException(message="Token is missing the orcid")
        if token_data.expiration < datetime.utcnow().timestamp():
            # TODO register token in db for requested expiration
            raise TokenException(message="Token is expired")
    except JWTError as e:
        raise TokenException(message=f"Exception occurred while decoding token [{str(e)}]")
    user: User = await User.find_one(User.orcid == token_data.orcid)
    if user is None:
        raise TokenException(message=f"No user found for orcid {token_data.orcid}")
    if not user.access_token:
        raise TokenException(message="Access token is missing")
    if user.access_token != token:
        raise TokenException(message="Access token is invalid")
    return user


async def get_current_user(settings=Depends(get_settings), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user = await get_user_from_token(token, settings)
    except TokenException as token_exception:
        credentials_exception.detail = token_exception.message
        raise credentials_exception
    await user.fetch_all_links()
    return user
