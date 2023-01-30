import json

from beanie import DeleteRules, WriteRules

from dspback.pydantic_schemas import User
from dspback.utils.jsonld.pydantic_schemas import JSONLD


async def delete_submission(identifier: str, user: User):
    submission = user.submission(identifier)
    await submission.delete(link_rule=DeleteRules.DELETE_LINKS)
    await JSONLD.find_one(JSONLD.repository_identifier == identifier).delete()


async def delete_repository_access_token(repository, user: User):
    repository_token = user.repository_token(repository)
    await repository_token.delete(link_rule=DeleteRules.DELETE_LINKS)


async def create_or_update_submission(identifier, submission, user: User, metadata_json):
    submission.metadata_json = json.dumps(metadata_json)
    existing_submission = user.submission(identifier)
    if existing_submission:
        existing_submission.update(submission.dict(exclude_unset=True))
        await existing_submission.save(link_rule=WriteRules.WRITE)
    else:
        user.submissions.append(submission)
        await user.save(link_rule=WriteRules.WRITE)
