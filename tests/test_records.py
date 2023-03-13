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


async def test_hydroshare_to_jsonld(hydroshare):
    hs_record = HydroShareRecord(**hydroshare)
    hs_jsonld = hs_record.to_jsonld("470e2ef676e947e5ab2628556c309122")

    assert hs_jsonld.url == get_settings().hydroshare_view_url % hs_record.identifier
    assert hs_jsonld.provider.name == 'HydroShare'
    assert hs_jsonld.name == hs_record.title
    assert hs_jsonld.description == hs_record.description
    assert hs_jsonld.keywords == hs_record.subjects
    assert hs_jsonld.temporalCoverage == hs_record.period_coverage
    assert hs_jsonld.spatialCoverage.geojson == hs_record.spatial_coverage.geojson
    assert hs_jsonld.creator.dict(by_alias=True) == {
        '@list': [{'name': creator.name} for creator in hs_record.creators]
    }
    assert hs_jsonld.license.dict() == {'text': hs_record.rights.statement}
    assert hs_jsonld.dict()['funding'] == [
        {"name": award.title, "number": award.number, "funder": {"name": award.funding_agency_name}}
        for award in hs_record.awards
    ]
    assert hs_jsonld.datePublished == hs_record.published
    assert hs_jsonld.dateCreated == hs_record.created
    assert hs_jsonld.relations == [relation.value for relation in hs_record.relations]


async def test_zenodo_to_submission(zenodo):
    zenodo_record = ZenodoRecord(**zenodo)
    zenodo_submission = zenodo_record.to_submission("947940")

    assert zenodo_submission.title == zenodo_record.title
    assert zenodo_submission.authors == [creator.name for creator in zenodo_record.creators]
    assert zenodo_submission.repo_type == RepositoryType.ZENODO
    assert zenodo_submission.submitted <= datetime.utcnow()
    assert zenodo_submission.identifier == zenodo_record.record_id
    assert zenodo_submission.url == get_settings().zenodo_view_url % zenodo_record.record_id


async def test_zenodo_to_jsonld(zenodo):
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
    assert zenodo_jsonld.funding[0].funder.name == zenodo_record.notes
    assert zenodo_jsonld.funding[0].name == zenodo_record.notes
    assert zenodo_jsonld.datePublished == zenodo_record.publication_date
    assert zenodo_jsonld.dateCreated == zenodo_record.created
    assert zenodo_jsonld.relations == [
        f'{relation.name} - {relation.identifier}' for relation in zenodo_record.relations
    ]


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
        {"name": funder.awardName, "number": funder.awardNumber, "funder": {"name": funder.fundingAgency}}
        for funder in external_record.funders
    ]
    assert external_jsonld.datePublished == external_record.datePublished
    assert external_jsonld.dateCreated == external_record.dateCreated
    assert external_jsonld.relations == [relation.value for relation in external_record.relations]


async def test_earthchem_to_submission(earthchem):
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


async def test_earthchem_to_jsonld(earthchem):
    ecl_record = EarthChemRecord(**earthchem)
    ecl_jsonld = ecl_record.to_jsonld("947940")

    assert ecl_jsonld.url == get_settings().earthchem_view_url % "947940"
    assert ecl_jsonld.provider.name == 'EarthChem Library'
    assert ecl_jsonld.name == ecl_record.title
    assert ecl_jsonld.description == ecl_record.description
    assert ecl_jsonld.keywords == ecl_record.keywords
    creators = [{'name': ecl_record.leadAuthor.name}] + [
        {'name': contributor.name} for contributor in ecl_record.contributors
    ]
    assert ecl_jsonld.creator.dict(by_alias=True) == {'@list': [creator for creator in creators]}
    assert ecl_jsonld.license.dict() == {'text': ecl_record.license.alternateName}
    assert ecl_jsonld.dict()['funding'] == [
        {"name": None, "number": funding.identifier, "funder": {"name": funding.funder.name}}
        for funding in ecl_record.fundings
    ]
    assert ecl_jsonld.datePublished == ecl_record.datePublished
    assert ecl_jsonld.relations == [relation.bibliographicCitation for relation in ecl_record.relatedResources]
