import json
from unittest.mock import patch
from urllib.parse import unquote

import pytest
from authlib.integrations.starlette_client import StarletteRemoteApp
from pydantic import BaseModel

from tests import (
    authorize_response,
    authorize_response_hydroshare,
    change_test_dir,
    client_test,
    external,
    prefix,
    user_cookie,
)


async def submission_check(client_test, access_token):
    response = await client_test.get(prefix + "/submissions?access_token=" + access_token)
    response_json = response.json()
    return response_json


async def new_external_record(client_test, user_cookie, external):
    response = await client_test.post(prefix + "/metadata/external?access_token=" + user_cookie, json=external)
    assert response.status_code == 201
    response_json = response.json()
    return response_json["metadata"]["identifier"]


async def test_create_external_record(client_test, user_cookie, external):
    assert len(await submission_check(client_test, user_cookie)) == 0

    assert len(await new_external_record(client_test, user_cookie, external)) == 36

    assert len(await submission_check(client_test, user_cookie)) == 1


@pytest.mark.skip
async def test_update_external_record(client_test, user_cookie, external):
    identifier = await new_external_record(client_test, user_cookie, external)

    external["name"] = "updated title"
    response = await client_test.put(
        prefix + "/metadata/external/" + identifier + "?access_token=" + user_cookie, json=external
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["name"] == "updated title"


async def test_get_external_record(client_test, user_cookie, external):
    identifier = await new_external_record(client_test, user_cookie, external)

    response = await client_test.get(prefix + "/metadata/external/" + identifier + "?access_token=" + user_cookie)

    assert response.json()["metadata"]["name"] == "string"


async def test_delete_external_record(client_test, user_cookie, external):
    identifier = await new_external_record(client_test, user_cookie, external)

    assert len(await submission_check(client_test, user_cookie)) == 1

    await client_test.delete(prefix + "/metadata/external/" + identifier + "?access_token=" + user_cookie)

    assert len(await submission_check(client_test, user_cookie)) == 0
