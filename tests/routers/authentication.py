from fastapi.testclient import TestClient

from authlib.integrations.starlette_client import StarletteRemoteApp
from dspback.config import oauth
from dspback.dependencies import url_for
from dspback.main import app

from urllib.parse import unquote
from unittest.mock import patch

from tests.routers import prefix, authorize_response


client = TestClient(app)


def test_home_not_logged_in():
    response = client.get(prefix)
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}


def test_login():
    response = client.get(prefix + "/login", allow_redirects=False)
    assert response.status_code == 302
    assert "response_type=code" in response.headers['location']
    assert "client_id=" in response.headers['location']
    assert f"redirect_uri={url_for(client, 'auth')}" in unquote(response.headers['location'])


def test_auth(authorize_response):
    # tests create user path
    with patch.object(StarletteRemoteApp, 'authorize_access_token', side_effect=[authorize_response]):
        response = client.get(prefix + "/auth", allow_redirects=False)
        assert response.status_code == 307
        assert 'Authorization="Bearer' in response.headers["set-cookie"]

    # tests update user path
    with patch.object(StarletteRemoteApp, 'authorize_access_token', side_effect=[authorize_response]):
        response = client.get(prefix + "/auth", allow_redirects=False)
        assert response.status_code == 307
        assert 'Authorization="Bearer' in response.headers["set-cookie"]


def test_logout():
    logout_response = client.get(prefix + "/logout", allow_redirects=False)
    assert 'Authorization=""' in logout_response.headers["set-cookie"]
    assert logout_response.is_redirect
    assert logout_response.headers['location'] == url_for(client, 'home')
