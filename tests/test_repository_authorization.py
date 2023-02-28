from unittest.mock import patch
from urllib.parse import unquote

import pytest
from authlib.integrations.starlette_client import StarletteRemoteApp

from dspback.dependencies import url_for
from tests import authorize_response, authorize_response_expired, change_test_dir, client_test, prefix, user_cookie


async def test_authorize_repository(client_test, user_cookie):
    response = await client_test.get(prefix + "/authorize/zenodo?access_token=" + user_cookie, follow_redirects=False)
    assert response.status_code == 302
    assert "response_type=code" in response.headers['location']
    assert "client_id=" in response.headers['location']
    redirect_uri = url_for(client_test, 'auth_repository', repository='zenodo')
    location = unquote(response.headers['location'])
    assert f"redirect_uri={redirect_uri}" in location


async def test_auth_repository(client_test, user_cookie, authorize_response):
    # test create_repository path
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response):
        response = await client_test.get(prefix + "/auth/zenodo?access_token=" + user_cookie, follow_redirects=False)
        assert response.status_code == 200

    # test update_repository path
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response):
        response = await client_test.get(prefix + "/auth/zenodo?access_token=" + user_cookie, follow_redirects=False)
        assert response.status_code == 200


async def test_get_access_token_not_found(client_test, user_cookie):
    response = await client_test.get(
        prefix + "/access_token/zenodo?access_token=" + user_cookie, follow_redirects=False
    )
    assert response.status_code == 404


async def test_get_access_token(client_test, user_cookie, authorize_response):
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response):
        response = await client_test.get(prefix + "/auth/zenodo?access_token=" + user_cookie, follow_redirects=False)

    response = await client_test.get(
        prefix + "/access_token/zenodo?access_token=" + user_cookie, follow_redirects=False
    )
    assert response.status_code == 200
    assert response.json()["access_token"] == "e6c2b3c2-c204-4199-a1c1-9b29e964b74b"


async def test_get_access_token_expired(client_test, user_cookie, authorize_response_expired):
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response_expired):
        response = await client_test.get(prefix + "/auth/zenodo?access_token=" + user_cookie, follow_redirects=False)

    response = await client_test.get(
        prefix + "/access_token/zenodo?access_token=" + user_cookie, follow_redirects=False
    )
    assert response.status_code == 404
