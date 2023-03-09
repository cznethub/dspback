import asyncio
import json
import logging
import re

import motor

from dspback.config import get_settings
from dspback.pydantic_schemas import ExternalRecord
from dspback.utils.jsonld.scraper import retrieve_discovery_jsonld


logger = logging.getLogger()

def sanitize(text):
    # remove urls form text
    text = re.sub(r'https?://\S+', '', text)

    # remove all single characters except "a"
    text = re.sub(r"\b[a-zA-Z](?<!a)\b", "", text)

    # replace parentheses and forward slash with space
    text = re.sub('[()/]', ' ', text)

    # remove double dashes
    text = re.sub('--', '', text)

    # remove special characters
    text = re.sub('[^a-zA-Z0-9,\- ]', '', text)

    # remove leading/trailing hyphens
    words = text.split(' ')
    for i in range(len(words)):
        words[i] = words[i].strip("-")
    text = " ".join(words)

    # remove extra spaces
    text = " ".join(text.split())

    return text


async def watch_discovery():
    db = motor.motor_asyncio.AsyncIOMotorClient(get_settings().mongo_url)[get_settings().mongo_database]
    async with db["discovery"].watch(full_document="updateLookup") as stream:
        async for change in stream:
            if change["operationType"] != "delete":
                document = change["fullDocument"]
                sanitized = {
                    '_id': document['_id'],
                    'name': sanitize(document['name']),
                    'description': sanitize(document['description']),
                    'keywords': [sanitize(keyword) for keyword in document['keywords']],
                }
                await db["typeahead"].find_one_and_replace({"_id": sanitized["_id"]}, sanitized, upsert=True)
            else:
                await db["typeahead"].delete_one({"_id": change["documentKey"]["_id"]})

async def watch_discovery_with_retry():
    while True:
        try:
            await watch_discovery()
        except:
            logger.exception("Discovery Watch Task failed, restarting the task after 1 second")
            await asyncio.sleep(1)


async def watch_submissions():
    db = motor.motor_asyncio.AsyncIOMotorClient(get_settings().mongo_url)[get_settings().mongo_database]
    async with db["Submission"].watch(full_document="updateLookup") as stream:
        async for change in stream:
            if change["operationType"] != "delete":
                document = change["fullDocument"]
                if document["repo_type"] == "external":
                    public_json_ld = (
                        ExternalRecord(**json.loads(document["metadata_json"])).to_jsonld(document["identifier"]).dict()
                    )
                else:
                    public_json_ld = await retrieve_discovery_jsonld(
                        document["identifier"], document["repo_type"], document["url"]
                    )

                if public_json_ld:
                    await db["discovery"].find_one_and_replace(
                        {"repository_identifier": public_json_ld["repository_identifier"]}, public_json_ld, upsert=True
                    )
                else:
                    await db["discovery"].delete_one({"_id": change["documentKey"]["_id"]})
            else:
                await db["discovery"].delete_one({"_id": change["documentKey"]["_id"]})


async def watch_submissions_with_retry():
    while True:
        try:
            await watch_submissions()
        except:
            logger.exception("Submission Watch Task failed, restarting the task after 1 second")
            await asyncio.sleep(1)
