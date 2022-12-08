import json
import os
from datetime import datetime

import pytest

from dspback.config import get_settings
from dspback.pydantic_schemas import EarthChemRecord, ExternalRecord, HydroShareRecord, RepositoryType, ZenodoRecord
from tests import change_test_dir, earthchem, external, hydroshare, zenodo


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


def test_hydroshare_to_jsonld(hydroshare):
    hs_record = HydroShareRecord(**hydroshare)
    hs_jsonld = hs_record.to_jsonld("470e2ef676e947e5ab2628556c309122")

    assert hs_jsonld.url == get_settings().hydroshare_view_url % hs_record.identifier
    assert hs_jsonld.provider.name == 'HydroShare'
    assert hs_jsonld.name == hs_record.title
    assert hs_jsonld.description == hs_record.description
    assert hs_jsonld.keywords == hs_record.subjects
    assert hs_jsonld.temporalCoverage == hs_record.period_coverage.dict()
    print(hs_jsonld.spatialCoverage.geojson)
    print(hs_record.spatial_coverage.geojson)
    assert hs_jsonld.spatialCoverage.geojson == hs_record.spatial_coverage.geojson
    assert hs_jsonld.creator.dict(by_alias=True) == {
        '@list': [{'name': creator.name} for creator in hs_record.creators]
    }
    assert hs_jsonld.license.dict() == {'text': hs_record.rights.statement}
    assert hs_jsonld.dict()['funding'] == [
        {"name": award.title, "number": award.number, "funder": [{"name": award.funding_agency_name}]}
        for award in hs_record.awards
    ]
    assert hs_jsonld.datePublished == hs_record.published
    assert hs_jsonld.dateCreated == hs_record.created
    assert hs_jsonld.relations == [relation.value for relation in hs_record.relations]


def test_zenodo_to_submission(zenodo):
    zenodo_record = ZenodoRecord(**zenodo)
    zenodo_submission = zenodo_record.to_submission("947940")

    assert zenodo_submission.title == zenodo_record.title
    assert zenodo_submission.authors == [creator.name for creator in zenodo_record.creators]
    assert zenodo_submission.repo_type == RepositoryType.ZENODO
    assert zenodo_submission.submitted <= datetime.utcnow()
    assert zenodo_submission.identifier == zenodo_record.record_id
    assert zenodo_submission.url == get_settings().zenodo_view_url % zenodo_record.record_id


def test_zenodo_to_jsonld(zenodo):
    zenodo_record = ZenodoRecord(**zenodo)
    zenodo_jsonld = zenodo_record.to_jsonld("947940")

    assert zenodo_jsonld.url == get_settings().zenodo_view_url % zenodo_record.record_id
    assert zenodo_jsonld.type == "Dataset"
    assert zenodo_jsonld.provider.name == "Zenodo"
    assert zenodo_jsonld.name == zenodo_record.title
    assert zenodo_jsonld.description == zenodo_record.description
    assert zenodo_jsonld.keywords == zenodo_record.keywords
    assert zenodo_jsonld.creator.dict(by_alias=True) == {
        '@list': [{'name': creator.name} for creator in zenodo_record.creators]
    }
    assert zenodo_jsonld.license.text == zenodo_record.license
    assert zenodo_jsonld.funding[0].funder[0].name == zenodo_record.notes
    assert zenodo_jsonld.funding[0].name == zenodo_record.notes
    assert zenodo_jsonld.datePublished == zenodo_record.publication_date
    assert zenodo_jsonld.dateCreated == zenodo_record.created
    assert zenodo_jsonld.relations == [
        f'{relation.name} - {relation.identifier}' for relation in zenodo_record.relations
    ]


def test_external_to_submission(external):
    external_record = ExternalRecord(**external)
    external_submission = external_record.to_submission("947940")

    assert external_submission.title == external_record.name
    assert external_submission.authors == [creator.name for creator in external_record.creators]
    assert external_submission.repo_type == RepositoryType.EXTERNAL
    assert external_submission.submitted <= datetime.utcnow()
    assert external_submission.identifier == "947940"
    assert external_submission.url == external_record.url


def test_earthchem_to_submission(earthchem):
    earthchem_record = EarthChemRecord(**earthchem)
    earthchem_submission = earthchem_record.to_submission("947940")

    assert earthchem_submission.title == earthchem_record.title
    authors = [f"{contributor.familyName}, {contributor.givenName}" for contributor in earthchem_record.contributors]
    authors.insert(0, f"{earthchem_record.leadAuthor.familyName}, {earthchem_record.leadAuthor.givenName}")
    assert earthchem_submission.authors == authors
    assert earthchem_submission.repo_type == RepositoryType.EARTHCHEM
    assert earthchem_submission.submitted <= datetime.utcnow()
    assert earthchem_submission.identifier == "947940"
    assert earthchem_submission.url == get_settings().earthchem_view_url % "947940"
