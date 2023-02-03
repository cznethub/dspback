from functools import lru_cache

from beanie import WriteRules
from pymongo import MongoClient

from dspback.config import get_settings
from dspback.pydantic_schemas import RepositoryType
from dspback.utils.jsonld.pydantic_schemas import JSONLD
from dspback.utils.jsonld.scraper import retrieve_discovery_jsonld


@lru_cache
def get_database():
    settings = get_settings()
    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(settings.mongo_url, tls=True, tlsAllowInvalidCertificates=True)

    # Create the database for our example (we will use the same database throughout the tutorial
    return client[settings.mongo_database][settings.mongo_collection]


async def upsert_discovery_entry(record, identifier):
    submission = record.to_submission(identifier)
    if submission.repo_type == RepositoryType.EXTERNAL:
        json_ld = record.to_jsonld(identifier)
    else:
        json_ld = await retrieve_discovery_jsonld(submission.identifier, submission.repo_type, submission.url)
    existing_jsonld = await JSONLD.find_one(JSONLD.repository_identifier == identifier)
    if existing_jsonld:
        if not json_ld:
            await existing_jsonld.delete()
        else:
            await existing_jsonld.set(json_ld.dict(exclude_unset=True))
    else:
        if json_ld:
            await json_ld.save(link_rule=WriteRules.WRITE)


async def delete_discovery_entry(identifier):
    await JSONLD.find_one(JSONLD.repository_identifier == identifier).delete()
