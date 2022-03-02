from urllib.parse import unquote

import pytest
from fastapi.testclient import TestClient

from dspback.dependencies import url_for
from dspback.main import app
from tests import authorize_response, change_test_dir, external, prefix, user_cookie

client = TestClient(app)


def submission_check(access_token):
    response = client.get(prefix + "/submissions?access_token=" + access_token)
    response_json = response.json()
    return len(response_json)


def new_record(user_cookie, external):
    response = client.post(prefix + "/metadata/external?access_token=" + user_cookie, json=external)
    response_json = response.json()
    return response_json["identifier"]


def test_create_external_record(user_cookie, external):
    assert submission_check(str(user_cookie)) == 0

    assert len(new_record(user_cookie, external)) == 36

    assert submission_check(str(user_cookie)) == 1


def test_update_external_record(user_cookie, external):
    identifier = new_record(user_cookie, external)

    external["name"] = "updated title"
    response = client.put(prefix + "/metadata/external/" + identifier + "?access_token=" + user_cookie, json=external)

    assert response.json()["name"] == "updated title"


def test_get_external_record(user_cookie, external):
    identifier = new_record(user_cookie, external)

    response = client.get(prefix + "/metadata/external/" + identifier + "?access_token=" + user_cookie)

    assert response.json()["name"] == "string"


def test_delete_external_record(user_cookie, external):
    identifier = new_record(user_cookie, external)

    assert submission_check(str(user_cookie)) == 1

    response = client.delete(prefix + "/metadata/external/" + identifier + "?access_token=" + user_cookie)

    assert submission_check(str(user_cookie)) == 0
