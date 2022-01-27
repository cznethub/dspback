from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session

from dspback.database.models import UserTable
from dspback.database.procedures import create_or_update_submission, delete_submission
from dspback.dependencies import get_current_user, get_db
from dspback.pydantic_schemas import HydroShareRecord, RepositoryType, ZenodoRecord, GitLabRecord

router = APIRouter()


record_type_by_repo_type = {RepositoryType.ZENODO: ZenodoRecord, RepositoryType.HYDROSHARE: HydroShareRecord}


def submit_record(db: Session, repository, identifier, user: UserTable, json_response):
    record = record_type_by_repo_type[repository](**json_response)
    submission = record.to_submission(identifier)
    create_or_update_submission(db, submission, user)
    return submission


@router.delete('/submit/{repository}/{identifier}')
async def delete_repository_record(
        repository: RepositoryType,
        identifier: str,
        user: UserTable = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    delete_submission(db, repository, identifier, user)


@router.get("/submissions")
async def get_submissions(user: UserTable = Depends(get_current_user)):
    return user.submissions
