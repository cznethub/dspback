import json
import os
from datetime import datetime

import pytest

from dspback.config import get_settings
from dspback.pydantic_schemas import ExternalRecord, HydroShareRecord, RepositoryType, ZenodoRecord
from tests import change_test_dir, external, hydroshare, zenodo


def test_hydroshare_to_submission(hydroshare):
    hs_record = HydroShareRecord(**hydroshare)
    hs_submission = hs_record.to_submission("470e2ef676e947e5ab2628556c309122")

    assert hs_submission.title == hs_record.title
    assert hs_submission.authors == [creator.name for creator in hs_record.creators]
    assert hs_submission.repo_type == RepositoryType.HYDROSHARE
    assert hs_submission.submitted <= datetime.utcnow()
    assert hs_submission.identifier == '470e2ef676e947e5ab2628556c309122'
    assert hs_submission.identifier == hs_record.identifier
    assert hs_submission.url == get_settings().hydroshare_view_url % hs_record.identifier


def test_zenodo_to_submission(zenodo):
    zenodo_record = ZenodoRecord(**zenodo)
    zenodo_submission = zenodo_record.to_submission("947940")

    assert zenodo_submission.title == zenodo_record.title
    assert zenodo_submission.authors == [creator.name for creator in zenodo_record.creators]
    assert zenodo_submission.repo_type == RepositoryType.ZENODO
    assert zenodo_submission.submitted <= datetime.utcnow()
    assert zenodo_submission.identifier == zenodo_record.record_id
    assert zenodo_submission.url == get_settings().zenodo_view_url % zenodo_record.record_id


def test_external_to_submission(external):
    external_record = ExternalRecord(**external)
    external_submission = external_record.to_submission("947940")

    assert external_submission.title == external_record.name
    assert external_submission.authors == [creator.name for creator in external_record.creators]
    assert external_submission.repo_type == RepositoryType.EXTERNAL
    assert external_submission.submitted <= datetime.utcnow()
    assert external_submission.identifier == "947940"
    assert external_submission.url == external_record.url
