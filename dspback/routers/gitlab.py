import httpx

from fastapi import APIRouter, HTTPException, Request
from fastapi.params import Depends
from hsmodels.schemas.resource import ResourceMetadataIn
from sqlalchemy.orm import Session
from starlette.responses import Response
from starlette.status import HTTP_204_NO_CONTENT, HTTP_201_CREATED

from dspback.database.models import UserTable, RepositoryTokenTable
from dspback.dependencies import get_current_user, get_db
from dspback.routers.submissions import get_record
from dspback.schemas import RepositoryType, GitLabRecord

router = APIRouter()

"""
    "create": "https://gitlab.com/api/v4/projects?ref=main",
    "update": "https://gitlab.com/api/v4/projects/%s/repository/files/.metadata.json?ref=main",
    "read": "https://gitlab.com/api/v4/projects/%s/repository/files/.metadata.json?ref=main",
"""


def get_user_gitlab_repository(user: UserTable = Depends(get_current_user),
                               db: Session = Depends(get_db)) -> RepositoryTokenTable:
    repo = user.repository_token(db, RepositoryType.GITLAB)
    if not repo:
        raise Exception("User has not authorized the gitlab repository")
    return repo


@router.post('/gitlab/metadata', status_code=HTTP_201_CREATED, name="create_gitlab_project_metadata")
async def create_gitlab_project_metadata(
        metadata: ResourceMetadataIn,
        request: Request,
        repository: RepositoryTokenTable = Depends(get_user_gitlab_repository)
):
    access_token = repository.access_token
    create_url = "https://gitlab.com/api/v4/projects"
    async with httpx.AsyncClient() as client:
        response = await client.post(create_url, data={"name": metadata.title, "description": metadata.abstract},
                                     params={"access_token": access_token})
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    identifier = response.json()["id"]

    await create_gitlab_metadata(identifier, metadata, request, repository)

    return {"id": identifier}


@router.post('/gitlab/metadata/{identifier}', status_code=HTTP_204_NO_CONTENT, response_class=Response, name="create_gitlab_metadata")
async def create_gitlab_metadata(
        identifier: str,
        metadata: ResourceMetadataIn,
        request: Request,
        repository: RepositoryTokenTable = Depends(get_user_gitlab_repository)):
    metadata_update_url = "https://gitlab.com/api/v4/projects/%s/repository/files/.metadata.json" % identifier

    async with httpx.AsyncClient() as client:
        response = await client.post(metadata_update_url,
                                     data={"branch": "main", "content": metadata.json(indent=2),
                                           "commit_message": "some automated message"},
                                     params={"access_token": repository.access_token})
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    await get_record(request, RepositoryType.GITLAB, identifier)


@router.put('/gitlab/metadata/{identifier}', status_code=HTTP_204_NO_CONTENT, response_class=Response, name="update_gitlab_metadata")
async def update_gitlab_metadata(
        identifier: str,
        metadata: ResourceMetadataIn,
        request: Request,
        repository: RepositoryTokenTable = Depends(get_user_gitlab_repository)):
    metadata_update_url = "https://gitlab.com/api/v4/projects/%s/repository/files/.metadata.json" % identifier
    async with httpx.AsyncClient() as client:
        response = await client.put(metadata_update_url,
                                    data={"branch": "main", "content": metadata.json(indent=2),
                                          "commit_message": "some automated message"},
                                    params={"access_token": repository.access_token})
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    await get_record(request, RepositoryType.GITLAB, identifier)


@router.get('/gitlab/metadata/{identifier}', response_model=ResourceMetadataIn)
async def get_gitlab_metadata(
        identifier: str,
        repository: RepositoryTokenTable = Depends(get_user_gitlab_repository)):
    metadata_read_url = "https://gitlab.com/api/v4/projects/%s/repository/files/.metadata.json" % identifier

    async with httpx.AsyncClient() as client:
        response = await client.get(metadata_read_url,
                                    params={"access_token": repository.access_token})

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    gitlab_record = GitLabRecord(**response.data)
    return gitlab_record.content
