from typing import Any

from fastapi import Request

from dspback.authentication.auth import create_or_update_user
from dspback.config import get_settings
from dspback.pydantic_schemas import User


def url_for(request: Request, name: str, **path_params: Any) -> str:
    url_path = request.app.url_path_for(name, **path_params)
    # TODO - get the parent router path instead of hardcoding /api
    return "https://{}{}".format(get_settings().outside_host, url_path)


async def get_current_user(request: Request) -> User:
    return await create_or_update_user(request.user_info['preferred_username'])
