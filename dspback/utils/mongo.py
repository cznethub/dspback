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
