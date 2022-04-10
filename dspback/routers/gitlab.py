import base64
import json

import requests
from fastapi import APIRouter, HTTPException
from fastapi_restful.cbv import cbv
from starlette.responses import JSONResponse

from dspback.database.procedures import delete_submission
from dspback.pydantic_schemas import RepositoryType
from dspback.routers.metadata_class import MetadataRoutes
from dspback.schemas.gitlab.model import ResourceMetadata

router = APIRouter()


@cbv(router)
class GitLabMetadataRoutes(MetadataRoutes):

    request_model = ResourceMetadata
    request_model_update = ResourceMetadata
    response_model = ResourceMetadata
    repository_type = RepositoryType.GITLAB

    @router.post('/metadata/gitlab', tags=["GitLab"])
    async def create_metadata_repository(self, metadata: request_model, identifier=None) -> response_model:
        if not identifier:
            response = requests.post(
                self.create_url,
                data={"name": metadata.title, "description": metadata.abstract},
                params={
                    "access_token": self.access_token,
                },
                timeout=15.0,
            )

            if response.status_code >= 300:
                raise HTTPException(status_code=response.status_code, detail=response.text)

            identifier = response.json()["id"]

        response = requests.post(
            self.update_url % identifier,
            data={"branch": "main", "content": metadata.json(indent=2), "commit_message": "some automated message"},
            params={
                "access_token": self.access_token,
            },
            timeout=15.0,
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = await self.get_metadata_repository(identifier)

        return JSONResponse(json_metadata, status_code=201)

    @router.put('/metadata/gitlab/{identifier}', tags=["GitLab"])
    async def update_metadata(self, metadata: request_model_update, identifier) -> response_model:
        existing_metadata = await self.get_metadata_repository(identifier)
        incoming_metadata = metadata.json(skip_defaults=True, exclude_unset=True)
        merged_metadata = {**existing_metadata, **json.loads(incoming_metadata)}
        response = requests.put(
            self.update_url % identifier,
            data={
                "branch": "main",
                "content": merged_metadata.json(indent=2),
                "commit_message": "some automated message",
            },
            params={
                "access_token": self.access_token,
            },
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return await self.get_metadata_repository(identifier)

    async def _retrieve_metadata_from_repository(self, identifier):
        def base64_decode(content):
            return str(base64.b64decode(content), "utf-8")

        response = requests.get(self.read_url % identifier + "?ref=main", params={"access_token": self.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = json.loads(base64_decode(json.loads(response.text)["content"]))
        return json_metadata

    @router.get('/metadata/gitlab/{identifier}', tags=["GitLab"])
    async def get_metadata_repository(self, identifier) -> response_model:
        json_metadata = await self._retrieve_metadata_from_repository(identifier)
        await self.submit(identifier=identifier, json_metadata=json_metadata)
        return json_metadata

    @router.delete('/metadata/gitlab/{identifier}', tags=["GitLab"])
    async def delete_metadata_repository(self, identifier):
        delete_submission(self.db, self.repository_type, identifier, self.user)

        response = requests.delete(
            self.delete_url % str(identifier),
            headers={"accept": "application/json", "Authorization": "Bearer " + str(self.access_token)},
        )
        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    @router.put('/submit/gitlab/{identifier}', name="submit", tags=["GitLab"])
    async def submit_repository_record(self, identifier: str):
        json_metadata = await self.submit(identifier)
        return json_metadata
