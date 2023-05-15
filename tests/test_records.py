import json
import os
from datetime import datetime

import pytest

from dspback.config import get_settings
from dspback.pydantic_schemas import ExternalRecord
from tests import change_test_dir, external


async def test_external_to_submission(external):
    external_record = ExternalRecord(**external)
    external_submission = external_record.to_submission("947940")

    assert external_submission.title == external_record.name
    assert external_submission.authors == [creator.name for creator in external_record.creators]
    assert external_submission.submitted <= datetime.utcnow()
    assert external_submission.identifier == "947940"
    assert external_submission.url == external_record.url


async def test_external_to_jsonld(external):
    external_record = ExternalRecord(**external)
    external_jsonld = external_record.to_jsonld("947940")

    assert external_jsonld.url == external_record.url
    assert external_jsonld.provider.name == external_record.provider.name
    assert external_jsonld.name == external_record.name
    assert external_jsonld.description == external_record.description
    assert external_jsonld.keywords == external_record.keywords
    assert external_jsonld.temporalCoverage == external_record.temporalCoverage
    assert external_jsonld.spatialCoverage.geojson == external_record.spatialCoverage.geojson
    assert external_jsonld.creator.dict(by_alias=True) == {
        '@list': [{'name': creator.name} for creator in external_record.creators]
    }
    assert external_jsonld.license.dict() == {'text': external_record.license.description}
    assert external_jsonld.dict()['funding'] == [
        {"name": funder.awardName, "identifier": funder.awardNumber, "funder": {"name": funder.fundingAgency}}
        for funder in external_record.funders
    ]
    assert external_jsonld.datePublished == external_record.datePublished
    assert external_jsonld.dateCreated == external_record.dateCreated
    assert external_jsonld.relations == [relation.value for relation in external_record.relations]
