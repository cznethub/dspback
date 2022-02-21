from unittest.mock import patch
from urllib.parse import unquote

from authlib.integrations.starlette_client import StarletteRemoteApp
from fastapi.testclient import TestClient

from dspback.dependencies import url_for
from dspback.main import app
from tests.routers import authorize_response, prefix

client = TestClient(app)


def test_home_not_logged_in():
    response = client.get(prefix)
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}


def test_login():
    response = client.get(url_for(client, 'login'), allow_redirects=False)
    assert response.status_code == 302
    assert "response_type=code" in response.headers['location']
    assert "client_id=" in response.headers['location']
    assert f"redirect_uri={url_for(client, 'auth')}" in unquote(response.headers['location'])


def test_auth(authorize_response):
    # tests create user path
    with patch.object(StarletteRemoteApp, 'authorize_access_token', side_effect=[authorize_response]):
        response = client.get(url_for(client, 'auth'), allow_redirects=False)
        assert response.status_code == 200

    # tests update user path
    with patch.object(StarletteRemoteApp, 'authorize_access_token', side_effect=[authorize_response]):
        response = client.get(url_for(client, 'auth'), allow_redirects=False)
        assert response.status_code == 200


def test_logout():
    # ensure use has an access token
    with patch.object(StarletteRemoteApp, 'authorize_access_token', side_effect=[authorize_response]):
        response = client.get(url_for(client, 'auth'), allow_redirects=False)
        assert response.status_code == 200

    logout_response = client.get(url_for(client, 'logout'), allow_redirects=False)
    assert 'Authorization=""' not in logout_response.headers["set-cookie"]
    assert logout_response.is_redirect
    assert logout_response.headers['location'] == "/"
