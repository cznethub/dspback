from unittest.mock import patch
from urllib.parse import unquote

from authlib.integrations.starlette_client import StarletteRemoteApp
from fastapi.testclient import TestClient

from dspback.dependencies import url_for
from dspback.main import app
from tests import authorize_response

client = TestClient(app)


def test_submissions_not_logged_in():
    response = client.get(url_for(client, "get_urls", repository="hydroshare"))
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


def test_logout(authorize_response):
    # ensure user has an access token
    with patch.object(StarletteRemoteApp, 'authorize_access_token', side_effect=[authorize_response]):
        login_response = client.get(url_for(client, 'auth'), allow_redirects=False)

    logged_in_response = client.get(url_for(client, "get_urls", repository="hydroshare"), allow_redirects=False)
    assert len(logged_in_response.text) is 30

    logout_response = client.get(url_for(client, 'logout'), allow_redirects=False)
    assert 'Authorization=""' not in logout_response.headers["set-cookie"]

    logged_out_response = client.get(url_for(client, "get_urls", repository="hydroshare"), allow_redirects=False)
    assert logged_out_response.status_code == 403
