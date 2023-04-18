import pytest

from tests import (
    authorize_response,
    authorize_response_other,
    change_test_dir,
    client_test,
    external,
    prefix,
    user_cookie,
    user_cookie_other,
)


async def test_submission_transfer(client_test, user_cookie, user_cookie_other, external):
    response = await client_test.post(prefix + "/metadata/external?access_token=" + user_cookie, json=external)
    assert response.status_code == 201

    response = await client_test.get(prefix + "/submissions?access_token=" + user_cookie)
    assert len(response.json()) == 1
    response = await client_test.get(prefix + "/submissions?access_token=" + user_cookie_other)
    assert len(response.json()) == 0

    await client_test.post(
        prefix
        + "/submissions/transfer?from_user_access_token="
        + user_cookie
        + "&to_user_access_token="
        + user_cookie_other
    )

    response = await client_test.get(prefix + "/submissions?access_token=" + user_cookie)
    assert len(response.json()) == 0
    response = await client_test.get(prefix + "/submissions?access_token=" + user_cookie_other)
    assert len(response.json()) == 1
