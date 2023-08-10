import json
from datetime import datetime

from beanie import DeleteRules, WriteRules

from dspback.config import get_settings
from dspback.pydantic_schemas import RepositoryType, Submission, User
from dspback.schemas.discovery import JSONLD


async def delete_submission(identifier: str, user: User):
    submission = user.submission(identifier)
    await submission.delete(link_rule=DeleteRules.DELETE_LINKS)


async def delete_repository_access_token(repository, user: User):
    repository_token = user.repository_token(repository)
    await repository_token.delete(link_rule=DeleteRules.DELETE_LINKS)


async def create_or_update_submission(identifier, record, user: User, metadata_json):
    submission = record.to_submission(identifier)
    submission.metadata_json = json.dumps(metadata_json, default=str)
    existing_submission = user.submission(identifier)
    if existing_submission:
        await existing_submission.set(submission.dict(exclude_unset=True))
    else:
        user.submissions.append(submission)
        await user.save(link_rule=WriteRules.WRITE)


async def create_or_update_submission_ecl_registration(user: User, jsonld, identifier):
    jsonld: JSONLD = JSONLD(**jsonld)
    submission = Submission(
        title=jsonld.name,
        authors=[creator.name for creator in jsonld.creator.list],
        repo_type=RepositoryType.EARTHCHEM,
        submitted=datetime.utcnow(),
        identifier=identifier,
        url=get_settings().earthchem_public_view_url % identifier,
    )
    existing_submission = user.submission(identifier)
    if existing_submission:
        await existing_submission.set(submission.dict(exclude_unset=True))
    else:
        user.submissions.append(submission)
        await user.save(link_rule=WriteRules.WRITE)
