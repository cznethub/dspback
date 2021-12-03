import json
import os

import pytest

from dspback.schemas import HydroShareRecord, RepositoryType, ZenodoRecord


@pytest.fixture(scope="function")
def change_test_dir(request):
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture
def hydroshare(change_test_dir):
    with open("data/hydroshare.json", "r") as f:
        return json.loads(f.read())


@pytest.fixture
def zenodo(change_test_dir):
    with open("data/zenodo.json", "r") as f:
        return json.loads(f.read())


def test_hydroshare_to_submission(hydroshare):
    hs_record = HydroShareRecord(**hydroshare)
    hs_submission = hs_record.to_submission()

    assert hs_submission.title == hs_record.title
    assert hs_submission.authors == [creator.name for creator in hs_record.creators]
    assert hs_submission.repo_type == RepositoryType.HYDROSHARE
    assert hs_submission.submitted == hs_record.modified
    assert hs_submission.identifier == '470e2ef676e947e5ab2628556c309122'


def test_zenodo_to_submission(zenodo):
    zenodo_record = ZenodoRecord(**zenodo)
    zenodo_submission = zenodo_record.to_submission()

    assert zenodo_submission.title == zenodo_record.title
    assert zenodo_submission.authors == [creator.name for creator in zenodo_record.creators]
    assert zenodo_submission.repo_type == RepositoryType.ZENODO
    assert zenodo_submission.submitted == zenodo_record.modified
    assert zenodo_submission.identifier == zenodo_record.record_id
