import httpx
import json

from fastapi import Request, APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session

from dspback.config import oauth, repository_config
from dspback.database.procedures import create_submission
from dspback.dependencies import get_current_user, get_db
from dspback.schemas import User, RepositoryType, ZenodoRecord, Submission

router = APIRouter()


# TODO change get to post
@router.get('/submission/{repository}/{submission_id}')
async def submit_repository_record(repository: RepositoryType, submission_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    read_url = repository_config[repository]["read"]
    read_url = read_url % (submission_id, )
    repo = user.repository_token(RepositoryType.ZENODO)
    access_token = repo.access_token
    async with httpx.AsyncClient() as client:
        response = await client.get(read_url, params={"access_token": access_token})
    json_response = json.loads(response.text)
    record = ZenodoRecord(**json_response)
    submission = record.to_submission()
    create_submission(db, submission, user)
    return submission


@router.get("/submissions")
async def get_submissions(user: User = Depends(get_current_user)):
    return user.submissions
