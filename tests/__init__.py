import json
import os
import secrets
from datetime import datetime, timedelta
from unittest.mock import patch

import motor
import pytest
from asgi_lifespan import LifespanManager
from authlib.integrations.starlette_client import StarletteRemoteApp
from beanie import init_beanie
from httpx import AsyncClient
from starlette.testclient import TestClient

from dspback.api import app
from dspback.config import get_settings
from dspback.pydantic_schemas import JSONLD, RepositoryToken, Submission, User

prefix = "/api"

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client_test():
    """
    Create an instance of the client.
    :return: yield HTTP client.
    """
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as ac:
            ac.app = app
            yield ac


@pytest.fixture
async def authorize_response():
    return {
        'access_token': 'e6c2b3c2-c204-4199-a1c1-9b29e964b74b',
        'token_type': 'bearer',
        'refresh_token': '52ecbb54-6c98-4f5a-b9fe-18a015eea4d0',
        'expires_in': 631138518,
        'scope': 'openid',
        'name': 'Scott',
        'orcid': secrets.token_hex(15),
        'id_token': 'eyJraWQiOiJzYW5kYm94LW9yY2lkLW9yZy0zaHBnb3NsM2I2bGFwZW5oMWV3c2dkb2IzZmF3ZXBvaiIsImFsZyI6IlJTMjU2In'
        '0.eyJhdF9oYXNoIjoidlpEZTFMMkFtY0dzVW4yQzh4OHU1ZyIsImF1ZCI6IkFQUC1ZUjkxOU5DSVIwVklOVkU3Iiwic3ViIjoi'
        'MDAwMC0wMDAyLTEwNTEtODUxMSIsImF1dGhfdGltZSI6MTYyNzA1MDY1MCwiaXNzIjoiaHR0cHM6XC9cL3NhbmRib3gub3JjaW'
        'Qub3JnIiwiZXhwIjoxNjI3MTQyODg5LCJnaXZlbl9uYW1lIjoiU2NvdHQiLCJpYXQiOjE2MjcwNTY0ODksIm5vbmNlIjoiVmpZ'
        'R1l6VmJuTWhUblZDNG9aYUIiLCJqdGkiOiJlYzRmZWE3Ny1lOTQzLTRlZTYtOGRmMS04OTkwY2NkMjcxMWQifQ.IJ1CXQNckUd'
        'LujXWn7UWCDVuhB8HjOwhbpf41UQHO3lljkLAs6BS1mWUzHFQi18uO3EBqlxcoBdLuL-mxa8jpnfHic154UW2vx6yP7ntnWqNi'
        'WyAf34ZI0ej8WyTPuRpQ0FFXplw1-KE1HO6qCcW137EW7gVjnzqI3cZuIw8BjQfr9fDx5kxSE6kzzYioEymOsTg5HGCPd9A9dT'
        'kaheGByOu9Ae188A4r0QEQQvtnfBNjv7sM4goQRHLmSL1cIkWEXgomNDZvMTXWx6Nwp0riT8wJ26qEbYwo3LSqpqFGlItx5j7N'
        'LSGfZ1DKb96HRlmuxbqHydLMQfAPrUMyqL3Kg',
        'expires_at': int(60 * 60 + datetime.utcnow().timestamp()),
    }


@pytest.fixture
async def authorize_response_other():
    return {
        'access_token': 'f6c2b3c2-c204-4199-a1c1-9b29e964b74b',
        'token_type': 'bearer',
        'refresh_token': '62ecbb54-6c98-4f5a-b9fe-18a015eea4d0',
        'expires_in': 631138518,
        'scope': 'openid',
        'name': 'ScottOther',
        'orcid': secrets.token_hex(15),
        'id_token': 'eyJraWQiOiJzYW5kYm94LW9yY2lkLW9yZy0zaHBnb3NsM2I2bGFwZW5oMWV3c2dkb2IzZmF3ZXBvaiIsImFsZyI6IlJTMjU2In'
        '0.eyJhdF9oYXNoIjoidlpEZTFMMkFtY0dzVW4yQzh4OHU1ZyIsImF1ZCI6IkFQUC1ZUjkxOU5DSVIwVklOVkU3Iiwic3ViIjoi'
        'MDAwMC0wMDAyLTEwNTEtODUxMSIsImF1dGhfdGltZSI6MTYyNzA1MDY1MCwiaXNzIjoiaHR0cHM6XC9cL3NhbmRib3gub3JjaW'
        'Qub3JnIiwiZXhwIjoxNjI3MTQyODg5LCJnaXZlbl9uYW1lIjoiU2NvdHQiLCJpYXQiOjE2MjcwNTY0ODksIm5vbmNlIjoiVmpZ'
        'R1l6VmJuTWhUblZDNG9aYUIiLCJqdGkiOiJlYzRmZWE3Ny1lOTQzLTRlZTYtOGRmMS04OTkwY2NkMjcxMWQifQ.IJ1CXQNckUd'
        'LujXWn7UWCDVuhB8HjOwhbpf41UQHO3lljkLAs6BS1mWUzHFQi18uO3EBqlxcoBdLuL-mxa8jpnfHic154UW2vx6yP7ntnWqNi'
        'WyAf34ZI0ej8WyTPuRpQ0FFXplw1-KE1HO6qCcW137EW7gVjnzqI3cZuIw8BjQfr9fDx5kxSE6kzzYioEymOsTg5HGCPd9A9dT'
        'kaheGByOu9Ae188A4r0QEQQvtnfBNjv7sM4goQRHLmSL1cIkWEXgomNDZvMTXWx6Nwp0riT8wJ26qEbYwo3LSqpqFGlItx5j7N'
        'LSGfZ1DKb96HRlmuxbqHydLMQfAPrUMyqL3Kh',
        'expires_at': int(60 * 60 + datetime.utcnow().timestamp()),
    }


@pytest.fixture
async def authorize_response_expired():
    return {
        'access_token': 'e6c2b3c2-c204-4199-a1c1-9b29e964b74b',
        'token_type': 'bearer',
        'refresh_token': '52ecbb54-6c98-4f5a-b9fe-18a015eea4d0',
        'expires_in': 631138518,
        'scope': 'openid',
        'name': 'Scott',
        'orcid': secrets.token_hex(15),
        'id_token': 'eyJraWQiOiJzYW5kYm94LW9yY2lkLW9yZy0zaHBnb3NsM2I2bGFwZW5oMWV3c2dkb2IzZmF3ZXBvaiIsImFsZyI6IlJTMjU2In'
        '0.eyJhdF9oYXNoIjoidlpEZTFMMkFtY0dzVW4yQzh4OHU1ZyIsImF1ZCI6IkFQUC1ZUjkxOU5DSVIwVklOVkU3Iiwic3ViIjoi'
        'MDAwMC0wMDAyLTEwNTEtODUxMSIsImF1dGhfdGltZSI6MTYyNzA1MDY1MCwiaXNzIjoiaHR0cHM6XC9cL3NhbmRib3gub3JjaW'
        'Qub3JnIiwiZXhwIjoxNjI3MTQyODg5LCJnaXZlbl9uYW1lIjoiU2NvdHQiLCJpYXQiOjE2MjcwNTY0ODksIm5vbmNlIjoiVmpZ'
        'R1l6VmJuTWhUblZDNG9aYUIiLCJqdGkiOiJlYzRmZWE3Ny1lOTQzLTRlZTYtOGRmMS04OTkwY2NkMjcxMWQifQ.IJ1CXQNckUd'
        'LujXWn7UWCDVuhB8HjOwhbpf41UQHO3lljkLAs6BS1mWUzHFQi18uO3EBqlxcoBdLuL-mxa8jpnfHic154UW2vx6yP7ntnWqNi'
        'WyAf34ZI0ej8WyTPuRpQ0FFXplw1-KE1HO6qCcW137EW7gVjnzqI3cZuIw8BjQfr9fDx5kxSE6kzzYioEymOsTg5HGCPd9A9dT'
        'kaheGByOu9Ae188A4r0QEQQvtnfBNjv7sM4goQRHLmSL1cIkWEXgomNDZvMTXWx6Nwp0riT8wJ26qEbYwo3LSqpqFGlItx5j7N'
        'LSGfZ1DKb96HRlmuxbqHydLMQfAPrUMyqL3Kg',
        'expires_at': int(datetime.utcnow().timestamp() - 61 * 60),
    }


@pytest.fixture
async def authorize_response_hydroshare():
    return {
        'access_token': 'ASbna3fKiyb2wZWZBKnIipircDPVwa',
        'expires_in': 2592000,
        'token_type': 'Bearer',
        'scope': 'read write',
        'refresh_token': 'lJtWoBkGwdfjRpg7PCu4R9XpPbYTG3',
        'expires_at': 1648834993,
    }


@pytest.fixture
async def user_cookie(client_test, authorize_response):
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response):
        response = await client_test.get(prefix + "/auth")
        assert response.status_code == 200
        return response.text


@pytest.fixture
async def user_cookie_other(client_test, authorize_response_other):
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response_other):
        response = await client_test.get(prefix + "/auth")
        assert response.status_code == 200
        return response.text


@pytest.fixture(scope="function")
async def change_test_dir(request):
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture
async def hydroshare(change_test_dir):
    with open("data/hydroshare.json", "r") as f:
        return json.loads(f.read())


@pytest.fixture
async def zenodo(change_test_dir):
    with open("data/zenodo.json", "r") as f:
        return json.loads(f.read())


@pytest.fixture
async def external(change_test_dir):
    with open("data/external.json", "r") as f:
        return json.loads(f.read())


@pytest.fixture
async def earthchem(change_test_dir):
    with open("data/earthchem.json", "r") as f:
        return json.loads(f.read())
