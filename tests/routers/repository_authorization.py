from unittest.mock import patch
from urllib.parse import unquote

import pytest

from authlib.integrations.starlette_client import StarletteRemoteApp
from fastapi.testclient import TestClient

from dspback.config import oauth
from dspback.dependencies import url_for
from dspback.main import app
from tests.routers import prefix, authorize_response

client = TestClient(app)


@pytest.fixture
def user_cookie(authorize_response):
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response):
        response = client.get(prefix + "/auth", allow_redirects=False)
        assert response.status_code == 307
        assert 'Authorization="Bearer' in response.headers["set-cookie"]
        return response.headers["set-cookie"]

def test_authorize_repository(user_cookie):
    response = client.get(prefix + "/authorize/zenodo", allow_redirects=False)
    assert response.status_code == 302
    assert "response_type=code" in response.headers['location']
    assert "client_id=" in response.headers['location']
    redirect_uri = url_for(client, 'auth_repository', repository='zenodo')
    location = unquote(response.headers['location'])
    assert f"redirect_uri={redirect_uri}" in location

def test_auth_repository(user_cookie, authorize_response):
    # test create_repository path
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response):
        response = client.get(prefix + "/auth/zenodo", allow_redirects=False)
        assert response.status_code == 307

    # test update_repository path
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response):
        response = client.get(prefix + "/auth/zenodo", allow_redirects=False)
        assert response.status_code == 307

def test_get_access_token_not_found(user_cookie):
    response = client.get(prefix + "/access_token/zenodo", allow_redirects=False)
    assert response.status_code == 404

def test_get_access_token(user_cookie, authorize_response):
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response):
        response = client.get(prefix + "/auth/zenodo", allow_redirects=False)

    response = client.get(prefix + "/access_token/zenodo", allow_redirects=False)
    assert response.status_code == 200
    assert response.json()["token"] == "e6c2b3c2-c204-4199-a1c1-9b29e964b74b"
