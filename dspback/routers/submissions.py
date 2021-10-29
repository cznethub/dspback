import httpx
import json

from fastapi import Request, APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from dspback.config import oauth, repository_config
from dspback.database.models import UserTable
from dspback.database.procedures import create_or_update_submission
from dspback.dependencies import get_current_user, get_db
from dspback.schemas import RepositoryType, ZenodoRecord, HydroShareRecord, SubmissionStatus

router = APIRouter()


record_type_by_repo_type = {RepositoryType.ZENODO: ZenodoRecord, RepositoryType.HYDROSHARE: HydroShareRecord}


async def save_submission(repository: RepositoryType, submission_id: str, status: SubmissionStatus, user: UserTable, db: Session):
    read_url = repository_config[repository]["read"]
    read_url = read_url % (submission_id,)
    repo = user.repository_token(db, repository)
    if not repo:
        raise Exception("User has not authorized the repository")
    access_token = repo.access_token
    async with httpx.AsyncClient() as client:
        response = await client.get(read_url, params={"access_token": access_token})
    json_response = json.loads(response.text)
    record = record_type_by_repo_type[repository](**json_response)
    submission = record.to_submission()
    submission.status = status
    create_or_update_submission(db, submission, user)
    return submission


# TODO change get to post
@router.get('/draft/{repository}/{submission_id}')
async def draft_repository_record(repository: RepositoryType, submission_id: str,
                                   user: UserTable = Depends(get_current_user), db: Session = Depends(get_db)):
    return await save_submission(repository, submission_id, SubmissionStatus.DRAFT, user, db)


# TODO change get to post
@router.get('/submit/{repository}/{submission_id}')
async def submit_repository_record(repository: RepositoryType, submission_id: str,
                                   user: UserTable = Depends(get_current_user), db: Session = Depends(get_db)):
    return await save_submission(repository, submission_id, SubmissionStatus.SUBMITTED, user, db)


@router.get("/submissions")
async def get_submissions(user: UserTable = Depends(get_current_user)):
    return user.submissions
