import json
import logging

import motor
from beanie import init_beanie
from rocketry import Rocketry
from rocketry.conds import daily

from dspback.config import get_settings
from dspback.pydantic_schemas import ExternalRecord, RepositoryType, Submission
from dspback.utils.jsonld.scraper import retrieve_discovery_jsonld

app = Rocketry(config={"task_execution": "async"})

logger = logging.getLogger()

async def retrieve_submission_json_ld(submission):
    if submission.repo_type != RepositoryType.EXTERNAL:
        public_json_ld = await retrieve_discovery_jsonld(
            submission.identifier, submission.repo_type, submission.url
        )
    else:
        public_json_ld = ExternalRecord(**json.loads(submission.metadata_json)).to_jsonld(submission.identifier).dict(by_alias=True)
    return public_json_ld


@app.task(daily)
async def do_daily():
    db = motor.motor_asyncio.AsyncIOMotorClient(get_settings().mongo_url)[get_settings().mongo_database]
    await init_beanie(database=db, document_models=[Submission])

    async for jsonld in db["discovery"].find({"legacy": False}):
        submission = await Submission.find_one(Submission.identifier == jsonld["repository_identifier"])
        if not submission:
            # remove
            await db["discovery"].delete_one({"repository_identifier": jsonld.repository_identifier})

    async for submission in Submission.find_all():
        try:
            public_json_ld = await retrieve_submission_json_ld(submission)
            if public_json_ld:
                await db["discovery"].find_one_and_replace(
                    {"repository_identifier": public_json_ld["repository_identifier"]}, public_json_ld, upsert=True
                )
        except:
            logger.exception(f"Failed to collect submission {submission.url}")


if __name__ == "__main__":
    # Run only Rocketry
    app.run()
