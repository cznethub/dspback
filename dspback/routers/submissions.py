import datetime

from fastapi import APIRouter
from fastapi.params import Depends

from dspback.database.procedures import create_or_update_submission, delete_submission
from dspback.dependencies import get_current_user
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
