import json
import os
from datetime import datetime

import pytest

from dspback.config import get_settings
from dspback.pydantic_schemas import EarthChemRecord, ExternalRecord, HydroShareRecord, RepositoryType, ZenodoRecord
from tests import change_test_dir, earthchem, external, hydroshare, zenodo


async def test_hydroshare_to_submission(hydroshare):
    hs_record = HydroShareRecord(**hydroshare)
    hs_submission = hs_record.to_submission("470e2ef676e947e5ab2628556c309122")

    assert hs_submission.title == hs_record.title
    assert hs_submission.authors == [creator.name for creator in hs_record.creators]
    assert hs_submission.repo_type == RepositoryType.HYDROSHARE
    assert hs_submission.submitted <= datetime.utcnow()
    assert hs_submission.identifier == '470e2ef676e947e5ab2628556c309122'
    assert hs_submission.identifier == hs_record.identifier
    assert hs_submission.url == get_settings().hydroshare_view_url % hs_record.identifier


async def test_zenodo_to_submission(zenodo):
    zenodo_record = ZenodoRecord(**zenodo)
    zenodo_record.publication_date = None
    zenodo_submission = zenodo_record.to_submission("947940")

    assert zenodo_submission.title == zenodo_record.title
    assert zenodo_submission.authors == [creator.name for creator in zenodo_record.creators]
    assert zenodo_submission.repo_type == RepositoryType.ZENODO
    assert zenodo_submission.submitted <= datetime.utcnow()
    assert zenodo_submission.identifier == zenodo_record.record_id
    assert zenodo_submission.url == get_settings().zenodo_view_url % zenodo_record.record_id


async def test_zenodo_published_to_submission(zenodo):
    zenodo_record = ZenodoRecord(**zenodo)
    zenodo_submission = zenodo_record.to_submission("947940")

    assert zenodo_submission.title == zenodo_record.title
    assert zenodo_submission.authors == [creator.name for creator in zenodo_record.creators]
    assert zenodo_submission.repo_type == RepositoryType.ZENODO
    assert zenodo_submission.submitted <= datetime.utcnow()
    assert zenodo_submission.identifier == zenodo_record.record_id
    assert zenodo_submission.url == get_settings().zenodo_public_view_url % zenodo_record.record_id


async def test_external_to_submission(external):
    external_record = ExternalRecord(**external)
    external_submission = external_record.to_submission("947940")

    assert external_submission.title == external_record.name
    assert external_submission.authors == [creator.name for creator in external_record.creators]
    assert external_submission.repo_type == RepositoryType.EXTERNAL
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


async def test_earthchem_to_submission(earthchem):
    earthchem_record = EarthChemRecord(**earthchem)
    earthchem_record.datePublished = None
    earthchem_submission = earthchem_record.to_submission("947940")

    assert earthchem_submission.title == earthchem_record.title
    authors = [f"{contributor.familyName}, {contributor.givenName}" for contributor in earthchem_record.contributors]
    authors.insert(0, f"{earthchem_record.leadAuthor.familyName}, {earthchem_record.leadAuthor.givenName}")
    assert earthchem_submission.authors == authors
    assert earthchem_submission.repo_type == RepositoryType.EARTHCHEM
    assert earthchem_submission.submitted <= datetime.utcnow()
    assert earthchem_submission.identifier == "947940"
    assert earthchem_submission.url == get_settings().earthchem_view_url % "947940"


async def test_earthchem_published_to_submission(earthchem):
    earthchem_record = EarthChemRecord(**earthchem)
    earthchem_submission = earthchem_record.to_submission("947940")

    assert earthchem_submission.title == earthchem_record.title
    authors = [f"{contributor.familyName}, {contributor.givenName}" for contributor in earthchem_record.contributors]
    authors.insert(0, f"{earthchem_record.leadAuthor.familyName}, {earthchem_record.leadAuthor.givenName}")
    assert earthchem_submission.authors == authors
    assert earthchem_submission.repo_type == RepositoryType.EARTHCHEM
    assert earthchem_submission.submitted <= datetime.utcnow()
    assert earthchem_submission.identifier == "947940"
    assert earthchem_submission.url == get_settings().earthchem_public_view_url % "947940"
