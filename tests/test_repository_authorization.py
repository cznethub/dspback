from unittest.mock import patch
from urllib.parse import unquote

import pytest
from authlib.integrations.starlette_client import StarletteRemoteApp
from fastapi.testclient import TestClient

from dspback.dependencies import url_for
from dspback.main import app
from tests import authorize_response, change_test_dir, client, prefix, user_cookie


def test_authorize_repository(user_cookie):
    response = client.get(prefix + "/authorize/zenodo?access_token=" + user_cookie, allow_redirects=False)
    assert response.status_code == 302
    assert "response_type=code" in response.headers['location']
    assert "client_id=" in response.headers['location']
    redirect_uri = url_for(client, 'auth_repository', repository='zenodo')
    location = unquote(response.headers['location'])
    assert f"redirect_uri={redirect_uri}" in location


def test_auth_repository(user_cookie, authorize_response):
    # test create_repository path
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response):
        response = client.get(prefix + "/auth/zenodo?access_token=" + user_cookie, allow_redirects=False)
        assert response.status_code == 200

    # test update_repository path
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response):
        response = client.get(prefix + "/auth/zenodo?access_token=" + user_cookie, allow_redirects=False)
        assert response.status_code == 200


def test_get_access_token_not_found(user_cookie):
    response = client.get(prefix + "/access_token/zenodo?access_token=" + user_cookie, allow_redirects=False)
    assert response.status_code == 404


def test_get_access_token(user_cookie, authorize_response):
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response):
        response = client.get(prefix + "/auth/zenodo?access_token=" + user_cookie, allow_redirects=False)

    response = client.get(prefix + "/access_token/zenodo?access_token=" + user_cookie, allow_redirects=False)
    assert response.status_code == 200
    assert response.json()["access_token"] == "e6c2b3c2-c204-4199-a1c1-9b29e964b74b"
