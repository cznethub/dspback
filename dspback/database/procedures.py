import asyncio
import json

from beanie import DeleteRules, WriteRules

from dspback.pydantic_schemas import User
from dspback.utils.jsonld.pydantic_schemas import JSONLD
from dspback.utils.mongo import delete_discovery_entry, retrieve_and_upsert_discovery_entry


async def delete_submission(identifier: str, user: User):
    submission = user.submission(identifier)
    await submission.delete(link_rule=DeleteRules.DELETE_LINKS)
    asyncio.get_event_loop().create_task(delete_discovery_entry(identifier))


async def delete_repository_access_token(repository, user: User):
    repository_token = user.repository_token(repository)
    await repository_token.delete(link_rule=DeleteRules.DELETE_LINKS)


async def create_or_update_submission(identifier, record, user: User, metadata_json):
    submission = record.to_submission(identifier)
    submission.metadata_json = json.dumps(metadata_json)
    existing_submission = user.submission(identifier)
    if existing_submission:
        await existing_submission.set(submission.dict(exclude_unset=True))
    else:
        user.submissions.append(submission)
        await user.save(link_rule=WriteRules.WRITE)

    asyncio.get_event_loop().create_task(retrieve_and_upsert_discovery_entry(record, identifier))
