from unittest.mock import patch
from urllib.parse import unquote

import pytest

from fastapi.testclient import TestClient

from dspback.config import oauth
from dspback.dependencies import url_for
from dspback.main import app
from tests.routers import prefix, authorize_response

client = TestClient(app)


@pytest.fixture
def user_cookie(authorize_response):

    with patch.object(oauth.orcid, 'authorize_access_token', side_effect=[authorize_response]):
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

def test_auth_repository(user_cookie):
    # test create_repository path
    with patch.object(oauth.zenodo, 'authorize_redirect', side_effect=[authorize_response]):
        response = client.get(prefix + "/auth/zenodo", allow_redirects=False)
        assert response.status_code == 307
        assert 'Authorization="Bearer' in response.headers["set-cookie"]

    # test update_repository path
    with patch.object(oauth.zenodo, 'authorize_redirect', side_effect=[authorize_response]):
        response = client.get(prefix + "/auth/zenodo", allow_redirects=False)
        assert response.status_code == 307
        assert 'Authorization="Bearer' in response.headers["set-cookie"]

