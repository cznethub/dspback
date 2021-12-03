import json

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session

from dspback.config import repository_config
from dspback.database.models import UserTable
from dspback.database.procedures import create_or_update_submission, delete_submission
from dspback.dependencies import get_current_user, get_db
from dspback.schemas import HydroShareRecord, RepositoryType, ZenodoRecord

router = APIRouter()


record_type_by_repo_type = {RepositoryType.ZENODO: ZenodoRecord, RepositoryType.HYDROSHARE: HydroShareRecord}


@router.put('/submit/{repository}/{submission_id}')
async def submit_repository_record(
    repository: RepositoryType,
    submission_id: str,
    user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    read_url = repository_config[repository]["read"]
    read_url = read_url % (submission_id,)
    repo = user.repository_token(db, repository)
    if not repo:
        raise Exception("User has not authorized the repository")
    access_token = repo.access_token
    async with httpx.AsyncClient() as client:
        response = await client.get(read_url, params={"access_token": access_token})
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    json_response = json.loads(response.text)
    record = record_type_by_repo_type[repository](**json_response)
    submission = record.to_submission()
    create_or_update_submission(db, submission, user)
    return submission


@router.delete('/submit/{repository}/{submission_id}')
async def delete_repository_record(
        repository: RepositoryType,
        submission_id: str,
        user: UserTable = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    delete_submission(db, repository, submission_id, user)



@router.get("/submissions")
async def get_submissions(user: UserTable = Depends(get_current_user)):
    return user.submissions
