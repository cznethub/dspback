import json

import requests
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session

from dspback.config import repository_config
from dspback.database.models import UserTable
from dspback.database.procedures import create_or_update_submission, delete_submission
from dspback.dependencies import get_current_user, get_db
from dspback.pydantic_schemas import HydroShareRecord, RepositoryType, ZenodoRecord, GitLabRecord

router = APIRouter()


record_type_by_repo_type = {RepositoryType.ZENODO: ZenodoRecord, RepositoryType.HYDROSHARE: HydroShareRecord,
                            RepositoryType.GITLAB: GitLabRecord}


def submit_record(db: Session, repository, identifier, user: UserTable, json_response):
    record = record_type_by_repo_type[repository](**json_response)
    submission = record.to_submission(identifier)
    create_or_update_submission(db, submission, user)
    return submission


@router.put('/submit/{repository}/{identifier}', name="submit")
async def submit_repository_record(
    repository: RepositoryType,
    identifier: str,
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    read_url = repository_config[repository]["read"]
    read_url = read_url % (identifier,)
    repo = user.repository_token(db, repository)
    if not repo:
        raise Exception("User has not authorized the repository")
    access_token = repo.access_token
    response = requests.get(read_url, params={"access_token": access_token})
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    json_response = json.loads(response.text)
    record = submit_record(db, repository, identifier, user, json_response)
    return record


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
