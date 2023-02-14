import json
from unittest.mock import patch
from urllib.parse import unquote

import pytest
from authlib.integrations.starlette_client import StarletteRemoteApp

from dspback.dependencies import url_for
from dspback.main import app
from tests import authorize_response, client_test


@pytest.mark.skip
async def test_submissions_not_logged_in(client_test):
    response = await client_test.get(url_for(client_test, "get_urls", repository="hydroshare"))
    assert response.json() == {"detail": "Not authenticated"}
    assert response.status_code == 403


async def test_login(client_test):
    response = await client_test.get(url_for(client_test, 'login'), follow_redirects=False)
    assert response.status_code == 302
    assert "response_type=code" in response.headers['location']
    assert "client_id=" in response.headers['location']
    assert f"redirect_uri={url_for(client_test, 'auth')}" in unquote(response.headers['location'])


async def test_auth(client_test, authorize_response):
    # tests create user path
    with patch.object(StarletteRemoteApp, 'authorize_access_token', side_effect=[authorize_response]):
        response = await client_test.get(url_for(client_test, 'auth'), follow_redirects=False)
        assert response.status_code == 200

    # tests update user path
    with patch.object(StarletteRemoteApp, 'authorize_access_token', side_effect=[authorize_response]):
        response = await client_test.get(url_for(client_test, 'auth'), follow_redirects=False)
        assert response.status_code == 200


@pytest.mark.skip
async def test_logout(client_test, authorize_response):
    # ensure user has an access token
    with patch.object(StarletteRemoteApp, 'authorize_access_token', side_effect=[authorize_response]):
        login_response = await client_test.get(url_for(client_test, 'auth'), follow_redirects=False)

    logged_in_response = await client_test.get(url_for(client_test, "get_urls", repository="hydroshare"))
    assert len(json.loads(logged_in_response.text)) == 18

    logout_response = await client_test.get(url_for(client_test, 'logout'), follow_redirects=False)
    assert 'Authorization=""' not in logout_response.headers["set-cookie"]

    logged_out_response = await client_test.get(
        url_for(client_test, "get_urls", repository="hydroshare"), follow_redirects=False
    )
    assert logged_out_response.status_code == 403
