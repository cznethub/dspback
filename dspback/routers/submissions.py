import datetime

from fastapi import APIRouter
from fastapi.params import Depends

from dspback.database.procedures import create_or_update_submission, delete_submission
from dspback.dependencies import get_current_user
from dspback.pydantic_schemas import (
    EarthChemRecord,
    ExternalRecord,
    HydroShareRecord,
    RepositoryType,
    User,
    ZenodoRecord,
)

router = APIRouter()


record_type_by_repo_type = {
    RepositoryType.ZENODO: ZenodoRecord,
    RepositoryType.HYDROSHARE: HydroShareRecord,
    RepositoryType.EXTERNAL: ExternalRecord,
    RepositoryType.EARTHCHEM: EarthChemRecord,
}


def convert_timestamp(item_date_object):
    if isinstance(item_date_object, (datetime.date, datetime.datetime)):
        return item_date_object.timestamp()


async def submit_record(repository, identifier, user: User, metadata_json):
    record = record_type_by_repo_type[repository](**metadata_json)
    return await create_or_update_submission(identifier, record, user, metadata_json)


@router.delete('/submit/{repository}/{identifier}')
async def delete_repository_record(repository: RepositoryType, identifier: str, user: User = Depends(get_current_user)):
    await delete_submission(identifier, user)


@router.get("/submissions")
async def get_submissions(user: User = Depends(get_current_user)):
    return user.submissions


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
