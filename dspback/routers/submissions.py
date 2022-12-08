import datetime
import json

from beanie import WriteRules
from dspback.dependencies import get_current_user
from fastapi import APIRouter
from fastapi.params import Depends

from dspback.utils.mongo import upsert_jsonld
from dspback.database.procedures import delete_submission
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
    submission = record.to_submission(identifier)
    submission.metadata_json = json.dumps(metadata_json)
    user.submissions.append(submission)
    await user.save(link_rule=WriteRules.WRITE)
    upsert_jsonld(record.to_jsonld(identifier))
    return submission


@router.delete('/submit/{repository}/{identifier}')
async def delete_repository_record(repository: RepositoryType, identifier: str, user: User = Depends(get_current_user)):
    await delete_submission(identifier, user)


@router.get("/submissions")
async def get_submissions(user: User = Depends(get_current_user)):
    return user.submissions
