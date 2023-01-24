from functools import lru_cache

from beanie import WriteRules
from pymongo import MongoClient

from dspback.config import get_settings
from dspback.utils.jsonld.pydantic_schemas import JSONLD


@lru_cache
def get_database():
    settings = get_settings()
    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(settings.mongo_url, tls=True, tlsAllowInvalidCertificates=True)

    # Create the database for our example (we will use the same database throughout the tutorial
    return client[settings.mongo_database][settings.mongo_collection]

async def upsert_jsonld(json_ld):
    existing_jsonld = await JSONLD.find_one(JSONLD.repository_identifier == json_ld.repository_identifier)
    if existing_jsonld:
        existing_jsonld.update(json_ld.dict(exclude_unset=True))
        await existing_jsonld.save(link_rule=WriteRules.WRITE)
    else:
        await json_ld.save(link_rule=WriteRules.WRITE)
