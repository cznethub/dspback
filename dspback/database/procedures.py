import json

from beanie import DeleteRules, WriteRules
from beanie.odm.operators.update.general import Set

from dspback.pydantic_schemas import User


async def create_or_update_user(preferred_username: str) -> User:
    await User.find_one(User.preferred_username == preferred_username)\
        .upsert(Set({'preferred_username': preferred_username}), on_insert=User(preferred_username=preferred_username))
    return await User.find_one(User.preferred_username == preferred_username)

async def delete_submission(identifier: str, user: User):
    submission = user.submission(identifier)
    await submission.delete(link_rule=DeleteRules.DELETE_LINKS)


async def create_or_update_submission(identifier, record, user: User, metadata_json):
    submission = record.to_submission(identifier)
    submission.metadata_json = json.dumps(metadata_json, default=str)
    existing_submission = user.submission(identifier)
    if existing_submission:
        await existing_submission.set(submission.dict(exclude_unset=True))
    else:
        user.submissions.append(submission)
        await user.save(link_rule=WriteRules.WRITE)
