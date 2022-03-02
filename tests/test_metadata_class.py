from urllib.parse import unquote

import pytest
from fastapi.testclient import TestClient

from dspback.dependencies import url_for
from dspback.main import app
from tests import authorize_response, change_test_dir, external, prefix, user_cookie

client = TestClient(app)


def submission_check(access_token):
    response = client.get(prefix + "/submissions?access_token=" + access_token, allow_redirects=False)
    response_json = response.json()
    return len(response_json)


def test_create_external_record(user_cookie, external):
    assert submission_check(str(user_cookie)) == 0

    response = client.post(
        prefix + "/metadata/external?access_token=" + user_cookie, allow_redirects=False, json=external
    )
    response_json = response.json()
    assert response_json["identifier"]
    assert response.status_code == 200

    assert submission_check(str(user_cookie)) == 1
