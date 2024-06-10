import asyncio
import logging
import re

import motor

from dspback.config import get_settings
from dspback.scheduler import retrieve_submission_json_ld

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
    text = re.sub('[^a-zA-Z0-9,\-_ ]', '', text)
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
            logger.debug(f"processing discovery watch for document: {change}")
            if change["operationType"] != "delete":
                document = change["fullDocument"]
                sanitized = {
                    '_id': document['_id'],
                    'name': sanitize(document['name']),
                    'description': sanitize(document['description']),
                    'keywords': [sanitize(keyword) for keyword in document['keywords']],
                }
                await db["typeahead"].find_one_and_replace({"_id": sanitized["_id"]}, sanitized, upsert=True)
                logger.debug(f"Updating {change['documentKey']['_id']}")
            else:
                await db["typeahead"].delete_one({"_id": change["documentKey"]["_id"]})
                logger.debug(f"Deleting {change['documentKey']['_id']}")


async def watch_discovery_with_retry():
    while True:
        try:
            await watch_discovery()
        except:
            logger.exception("Discovery Watch Task failed, restarting the task after 1 second")
            await asyncio.sleep(1)


async def watch_submissions():
    logger.info(f"Starting watching Submissions")
    db = motor.motor_asyncio.AsyncIOMotorClient(get_settings().mongo_url)[get_settings().mongo_database]
    async with db["Submission"].watch(
        full_document="updateLookup", full_document_before_change="whenAvailable"
    ) as stream:
        async for change in stream:
            logger.debug(f"processing submission watch for document: {change}")
            if change["operationType"] != "delete":
                document = change["fullDocument"]
                public_json_ld = await retrieve_submission_json_ld(document)

                if public_json_ld:
                    logger.debug(f"Found public jsonld, updating the discovery record for {document['identifier']}")
                    await db["discovery"].find_one_and_replace(
                        {"repository_identifier": public_json_ld["repository_identifier"]}, public_json_ld, upsert=True
                    )
                else:
                    logger.debug(f"No public jsonld found, deleting the discovery record for {document['identifier']}")
                    result = await db["discovery"].delete_one({"repository_identifier": document["identifier"]})
                    logger.warning(f"delete count {result.deleted_count}")
            else:
                logger.debug(f"Deleting the discovery record for {document['identifier']}")
                document = change["fullDocumentBeforeChange"]
                await db["discovery"].delete_one({"repository_identifier": document["identifier"]})


async def watch_submissions_with_retry():
    while True:
        try:
            await watch_submissions()
        except:
            logger.exception("Submission Watch Task failed, restarting the task after 1 second")
            await asyncio.sleep(1)
