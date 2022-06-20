from unittest.mock import patch
from urllib.parse import unquote

import pytest
from authlib.integrations.starlette_client import StarletteRemoteApp
from fastapi.testclient import TestClient

from dspback.dependencies import url_for
from dspback.main import app
from tests import (
    authorize_response,
    authorize_response_hydroshare,
    change_test_dir,
    external,
    hydroshare,
    prefix,
    user_cookie,
)

client = TestClient(app)


def submission_check(access_token):
    response = client.get(prefix + "/submissions?access_token=" + access_token)
    response_json = response.json()
    return response_json


def new_external_record(user_cookie, external):
    response = client.post(prefix + "/metadata/external?access_token=" + user_cookie, json=external)
    assert response.status_code == 201
    response_json = response.json()
    return response_json["identifier"]


def test_create_external_record(user_cookie, external):
    assert len(submission_check(user_cookie)) == 0

    assert len(new_external_record(user_cookie, external)) == 36

    assert len(submission_check(user_cookie)) == 1


def test_update_external_record(user_cookie, external):
    identifier = new_external_record(user_cookie, external)

    external["name"] = "updated title"
    response = client.put(prefix + "/metadata/external/" + identifier + "?access_token=" + user_cookie, json=external)

    assert response.json()["name"] == "updated title"


def test_get_external_record(user_cookie, external):
    identifier = new_external_record(user_cookie, external)

    response = client.get(prefix + "/metadata/external/" + identifier + "?access_token=" + user_cookie)

    assert response.json()["name"] == "string"


def test_delete_external_record(user_cookie, external):
    identifier = new_external_record(user_cookie, external)

    assert len(submission_check(user_cookie)) == 1

    client.delete(prefix + "/metadata/external/" + identifier + "?access_token=" + user_cookie)

    assert len(submission_check(user_cookie)) == 0


'''
def new_hydroshare_record(user_cookie, hydroshare, authorize_response_hydroshare):
    # patch the access token for the repository
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response_hydroshare):
        response = client.get(prefix + "/auth/hydroshare?access_token=" + user_cookie, allow_redirects=False)
    response = client.get(prefix + "/access_token/hydroshare?access_token=" + user_cookie, allow_redirects=False)

    # patch the call to HydroShre
    with patch.object(StarletteRemoteApp, 'authorize_access_token', return_value=authorize_response_hydroshare):
        response = client.get(prefix + "/auth/hydroshare?access_token=" + user_cookie, allow_redirects=False)
    response = client.get(prefix + "/access_token/hydroshare?access_token=" + user_cookie, allow_redirects=False)

    # create the record
    response = client.post(prefix + "/metadata/hydroshare?access_token=" + user_cookie, json=hydroshare)
    response_json = response.json()
    return response_json["identifier"]


def test_create_hydroshare_record(user_cookie, hydroshare, authorize_response_hydroshare):
    assert submission_check(str(user_cookie)) == 0

    assert len(new_hydroshare_record(user_cookie, hydroshare, authorize_response_hydroshare)) == 68

    assert submission_check(str(user_cookie)) == 1
'''


def test_unauthorized_hydroshare(user_cookie, hydroshare):
    response = client.post(prefix + "/metadata/hydroshare?access_token=" + user_cookie, json=hydroshare)
    assert response.status_code == 403
    assert response.text == '{"detail":"User has not authorized with hydroshare"}'
