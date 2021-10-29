import json
import os
from datetime import datetime

import pytest

from dspback.schemas import HydroShareRecord, RepositoryType, SubmissionStatus


@pytest.fixture(scope="function")
def change_test_dir(request):
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture
def hydroshare(change_test_dir):
    with open("data/hydroshare.json", "r") as f:
        return json.loads(f.read())

def test_hydroshare_to_submission(hydroshare):
    hs_record = HydroShareRecord(**hydroshare)
    hs_submission = hs_record.to_submission()

    assert hs_submission.title == hs_record.title
    assert hs_submission.authors == [creator.name for creator in hs_record.creators]
    assert hs_submission.repo_type == RepositoryType.HYDROSHARE
    assert hs_submission.status == SubmissionStatus.DRAFT
    assert hs_submission.submitted == hs_record.modified
    assert hs_submission.identifier == '470e2ef676e947e5ab2628556c309122'


