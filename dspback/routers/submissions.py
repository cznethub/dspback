import datetime

from beanie import WriteRules
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from starlette import status

from dspback.config import get_settings
from dspback.database.procedures import create_or_update_submission, delete_submission
from dspback.dependencies import TokenException, get_current_user, get_user_from_token
from dspback.pydantic_schemas import (
    ExternalRecord,
    User,
)

router = APIRouter()


def convert_timestamp(item_date_object):
    if isinstance(item_date_object, (datetime.date, datetime.datetime)):
        return item_date_object.timestamp()


async def submit_record(identifier, user: User, metadata_json):
    record = ExternalRecord(**metadata_json)
    return await create_or_update_submission(identifier, record, user, metadata_json)


@router.delete('/submit/{repository}/{identifier}')
async def delete_repository_record(identifier: str, user: User = Depends(get_current_user)):
    await delete_submission(identifier, user)


@router.get("/submissions")
async def get_submissions(user: User = Depends(get_current_user)):
    return user.submissions


async def get_user(token, settings) -> User:
    try:
        user = await get_user_from_token(token, settings)
    except TokenException as token_exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=token_exception.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    await user.fetch_all_links()
    return user


@router.post("/submissions/transfer")
async def transfer_submissions(from_user_access_token: str, to_user_access_token: str, settings=Depends(get_settings)):
    from_user: User = await get_user(from_user_access_token, settings)
    to_user: User = await get_user(to_user_access_token, settings)
    to_user.submissions.extend(from_user.submissions)
    await to_user.save(link_rule=WriteRules.WRITE)
    from_user.submissions.clear()
    await from_user.save(link_rule=WriteRules.WRITE)


# The below commented out code was used for testing and debugging, keeping for later use
'''
from beanie import WriteRules
from pydantic import AnyUrl, BaseModel
from dspback.utils.jsonld.pydantic_schemas import JSONLD
from dspback.utils.jsonld.scraper import retrieve_discovery_jsonld
from dspback.utils.mongo import upsert_discovery_entry

class RegisterModel(BaseModel):
    url: AnyUrl

@router.post('/register/{repository}/{identifier}')
async def register_record_with_discovery(body: RegisterModel, repository: RepositoryType, identifier):
    return await update_record_with_discovery(body, repository, identifier)

@router.put('/register/{repository}/{identifier}')
async def update_record_with_discovery(body: RegisterModel, repository: RepositoryType, identifier):
    json_ld = await retrieve_discovery_jsonld(identifier, repository, body.url)
    existing_jsonld = await JSONLD.find_one(JSONLD.repository_identifier == identifier)
    if existing_jsonld:
        if not json_ld:
            await existing_jsonld.delete()
        else:
            await existing_jsonld.set(json_ld.dict(exclude_unset=True))
    else:
        await json_ld.save(link_rule=WriteRules.WRITE)
    return json_ld
@router.delete('/register/{repository}/{identifier}')
async def deregister_record_with_discovery(repository: RepositoryType, identifier):
    json_ld = await JSONLD.find_one(JSONLD.repository_identifier == identifier)
    if json_ld:
        await json_ld.delete()
    return json_ld
'''
