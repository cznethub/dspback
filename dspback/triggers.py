import logging
import re

import motor

from dspback.config import get_settings

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
            document = change["fullDocument"]
            sanitized = {
                '_id': document['_id'],
                'name': sanitize(document['name']),
                'description': sanitize(document['description']),
                'keywords': [sanitize(keyword) for keyword in document['keywords']],
            }
            await db["typeahead"].find_one_and_replace({"_id": sanitized["_id"]}, sanitized, upsert=True)
