import asyncio
from dspback.pydantic_schemas import RepositoryType, ZenodoRecord

import motor
import json
from beanie import init_beanie

from dspback.config import get_settings
from dspback.pydantic_schemas import Submission

'''
This python script updates the ECL submission urls.

Example call:

docker exec dspback python management/refresh_submission_url_zenodo.py
'''

async def initiaize_beanie():
    db = motor.motor_asyncio.AsyncIOMotorClient(get_settings().mongo_url)
    await init_beanie(
        database=db[get_settings().mongo_database], document_models=[Submission]
    )

async def main():
    await initiaize_beanie()

    count = 0
    for submission in await Submission.find(Submission.repo_type == RepositoryType.ZENODO).to_list():
        metadata_json = json.loads(submission.metadata_json)
        refreshed_submission = ZenodoRecord(metadata_json).to_submission(submission.identifier)
        print(f"updating {submission.url}")
        submission.url = refreshed_submission.url
        await submission.save()
        print(f"to {submission.url}")
        count = count + 1
    print(f"total submission updated {count}")


if __name__ == "__main__":
    asyncio.run(main())