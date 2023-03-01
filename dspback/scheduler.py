import motor
from beanie import init_beanie
from rocketry import Rocketry
from rocketry.conds import daily

from dspback.config import get_settings
from dspback.pydantic_schemas import RepositoryType, Submission
from dspback.utils.jsonld.pydantic_schemas import JSONLD
from dspback.utils.jsonld.scraper import retrieve_discovery_jsonld
from dspback.utils.mongo import upsert_discovery_entry

app = Rocketry(config={"task_execution": "async"})


# @app.task(daily)
@app.task(daily)
async def do_daily():
    db = motor.motor_asyncio.AsyncIOMotorClient(get_settings().mongo_url)
    await init_beanie(database=db[get_settings().mongo_database], document_models=[JSONLD])
    async for jsonld in JSONLD.find_all():
        submission = await Submission.find_one(Submission.identifier == jsonld.repository_identifier)
        if not submission:
            # remove
            await JSONLD.find_one(JSONLD.repository_identifier == submission.identifier).delete()

    async for submission in Submission.find_all():
        if submission.repo_type != RepositoryType.EXTERNAL:
            public_json_ld = await retrieve_discovery_jsonld(
                submission.identifier, submission.repo_type, submission.url
            )
            await upsert_discovery_entry(public_json_ld, submission.identifier)


if __name__ == "__main__":
    # Run only Rocketry
    app.run()
