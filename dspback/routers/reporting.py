from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette import status

from dspback.database.models import UserTable
from dspback.database.procedures import submissions_report_json
from dspback.dependencies import get_current_user, get_db

router = APIRouter()


@router.get("/reporting")
async def get_reporting(user: UserTable = Depends(get_current_user), db: Session = Depends(get_db)):
    #if user.orcid not in [""]:
    #    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return submissions_report_json(db)
