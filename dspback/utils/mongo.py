from functools import lru_cache

from pymongo import MongoClient

from dspback.config import get_settings


@lru_cache
def get_database():
    settings = get_settings()
    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(settings.mongo_url, tls=True, tlsAllowInvalidCertificates=True)

    # Create the database for our example (we will use the same database throughout the tutorial
    return client[settings.mongo_database][settings.mongo_collection]


def upsert_jsonld(json_ld):
    collection = get_database()
    id_filter = {'@repository_identifier': json_ld['@repository_identifier']}
    collection.update_one(id_filter, {'$set': json_ld}, upsert=True)


def delete_jsonld(identifier):
    collection = get_database()
    id_filter = {'@repository_identifier': identifier}
    collection.delete_one(id_filter)
