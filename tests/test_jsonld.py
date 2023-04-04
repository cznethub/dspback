import json

import pytest
from pydantic import BaseModel

from dspback.pydantic_schemas import RepositoryType, Submission
from dspback.scheduler import retrieve_submission_json_ld
from dspback.utils.jsonld.clusters import clusters

ids_and_cluster = [
    ("2012073", "Bedrock Cluster"),
    ("2012264", "Bedrock Cluster"),
    ("2012357", "Bedrock Cluster"),
    ("2012316", "Bedrock Cluster"),
    ("2012353", "Bedrock Cluster"),
    ("2012227", "Bedrock Cluster"),
    ("2012408", "Bedrock Cluster"),
    ("2011439", "Big Data Cluster"),
    ("2012123", "Big Data Cluster"),
    ("2012188", "Big Data Cluster"),
    ("2011346", "Big Data Cluster"),
    ("2012080", "Big Data Cluster"),
    ("2012484", "Coastal Cluster"),
    ("2012322", "Coastal Cluster"),
    ("2012670", "Coastal Cluster"),
    ("2011941", "Coastal Cluster"),
    ("2012319", "Coastal Cluster"),
    ("2012475", "Drylands Cluster"),
    ("2012082", "Dust^2 Cluster"),
    ("2011910", "Dust^2 Cluster"),
    ("2012067", "Dust^2 Cluster"),
    ("2012093", "Dust^2 Cluster"),
    ("2012091", "Dust^2 Cluster"),
    ("2012669", "Dynamic Water Cluster"),
    ("2012821", "Dynamic Water Cluster"),
    ("2012796", "Dynamic Water Cluster"),
    ("2012730", "Dynamic Water Cluster"),
    ("2012310", "Dynamic Water Cluster"),
    ("2012878", "GeoMicroBio Cluster"),
    ("2012403", "GeoMicroBio Cluster"),
    ("2012633", "GeoMicroBio Cluster"),
    ("2217532", "GeoMicroBio Cluster"),
    ("2012409", "Urban Cluster"),
    ("2012616", "Urban Cluster"),
    ("2012336", "Urban Cluster"),
    ("2012107", "Urban Cluster"),
    ("2012340", "Urban Cluster"),
    ("2012313", "Urban Cluster"),
    ("2012344", "Urban Cluster"),
    ("2011617", "Urban Cluster"),
    ("2012593", "CZNet Hub"),
    ("2012893", "CZNet Hub"),
    ("2012748", "CZNet Hub"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("identifier,cluster", ids_and_cluster)
async def test_clusters(identifier, cluster):
    jsonld = {"funding": [{"number": identifier}]}
    matched_clusters = clusters(jsonld)
    assert len(matched_clusters) == 1
    assert cluster in matched_clusters


@pytest.mark.asyncio
async def test_substring_match():
    jsonld = {"funding": [{"number": "EAR 2012073 EAR"}]}
    matched_clusters = clusters(jsonld)
    assert len(matched_clusters) == 1
    assert "Bedrock Cluster" in matched_clusters


@pytest.mark.asyncio
async def test_multiple_same_cluster():
    jsonld = {"funding": [{"number": "2012073"}, {"number": "2012264"}]}
    matched_clusters = clusters(jsonld)
    assert len(matched_clusters) == 1
    assert "Bedrock Cluster" in matched_clusters


@pytest.mark.asyncio
async def test_many_clusters():
    jsonld = {"funding": [{"number": "2012073"}, {"number": "2012264"}, {"number": "2011439"}]}
    matched_clusters = clusters(jsonld)
    assert len(matched_clusters) == 2
    assert "Bedrock Cluster" in matched_clusters
    assert "Big Data Cluster" in matched_clusters


@pytest.mark.asyncio
async def test_external_jsonld():
    metadata_json = {
        "name": "Dryland Critical Zone: Jornada Piedmont Seismic Imaging",
        "description": "As part of an NSF-funded Dryland Critical Zone project, we are collecting a 3-km active source seismic line in the Jornada Long Term Ecological Research site for shallow reflection and refraction imaging. Sources will be from the A200 weight drop, provided by the Seismic Source Facility at UTEP, and receivers will be 300 3-component nodes (200 requested from PASSCAL). With this survey, we are aiming to identify and map faults and other structures in the shallow subsurface. From gravity modeling and surface mapping, we expect to image several normal faults along this line. The nodes will be left in the field as long as possible (up to 30 days) for ambient noise imaging and also analyses of connections between weather (especially high wind events) and seismic signals as part of a DoD-funded project entitled \"Desert Seismology: Linking weather, saltating particles, and dryland geomorphology to the ambient seismic environment\".",
        "keywords": ["CZNet", "Dryland Critical Zone", "Seismic", "Jornada Experimental Range"],
        "creators": [
            {
                "name": "asdf Karplus",
                "organization": "University of Texas at El Paso (UTEP)",
                "email": "mkarplus@mail",
                "orcid": "0000-0001-2345-6789",
            }
        ],
        "contributors": [],
        "license": None,
        "funders": [
            {
                "fundingAgency": "National Science Foundation ",
                "awardNumber": "2012475",
                "awardName": "Critical Zone Collaborative Network, Dryland Thematic Cluster",
                "awardURL": None,
            }
        ],
        "relations": None,
        "version": "These dates only reflect year.  Start year:  2021, End year:  2021, Published:  2021",
        "url": "https://doi.org/10.7914/SN/9D_2021",
        "identifier": "29c95cd6-85bd-4044-a4eb-48c40c7fb5a1",
        "temporalCoverage": None,
        "spatialCoverage": None,
        "provider": {"name": "IRIS Data Management Center", "url": "http://service.iris.edu/ph5ws/dataselect/1/"},
        "dateCreated": "2021-01-01T00:00:00-07:00",
        "dateModified": "2021-01-01T00:00:00-07:00",
        "datePublished": "2021-01-01T00:00:00-07:00",
    }

    class MockSubmission(BaseModel):
        repo_type: RepositoryType
        metadata_json: str
        identifier: str

    submission = MockSubmission(
        repo_type=RepositoryType.EXTERNAL, metadata_json=json.dumps(metadata_json), identifier="id"
    )
    public_jsonld = await retrieve_submission_json_ld(submission)
    assert len(public_jsonld["clusters"]) == 1
    assert public_jsonld["clusters"][0] == "Drylands Cluster"
