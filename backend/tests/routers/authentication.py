import secrets

import pytest
from fastapi.testclient import TestClient

from backend.config import oauth
from backend.dependencies import url_for
from backend.main import app

from urllib.parse import unquote
from unittest.mock import patch

client = TestClient(app)

prefix = "/api"

# TODO - cleanup the database


@pytest.fixture
def authorize_response():
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
        'expires_at': 2258195007
    }


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
    with patch.object(oauth.orcid, 'authorize_access_token', side_effect=[authorize_response]):
        response = client.get(prefix + "/auth", allow_redirects=False)
        assert response.status_code == 307
        assert 'Authorization="Bearer' in response.headers["set-cookie"]

    # tests update user path
    with patch.object(oauth.orcid, 'authorize_access_token', side_effect=[authorize_response]):
        response = client.get(prefix + "/auth", allow_redirects=False)
        assert response.status_code == 307
        assert 'Authorization="Bearer' in response.headers["set-cookie"]


def test_logout():
    logout_response = client.get(prefix + "/logout", allow_redirects=False)
    assert 'Authorization=""' in logout_response.headers["set-cookie"]
    assert logout_response.is_redirect
    assert logout_response.headers['location'] == url_for(client, 'home')
