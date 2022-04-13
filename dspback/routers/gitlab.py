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
    async def create_metadata_repository(
        self, metadata: request_model, identifier=None, branch: str = "main"
    ) -> response_model:
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
        return await self.create_metadata_aggregation(metadata, identifier, branch)

    @router.post('/metadata/gitlab/{identifier}', tags=["GitLab"])
    async def create_metadata_aggregation(
        self, metadata: request_model, identifier=None, branch: str = "main"
    ) -> response_model:

        response = requests.post(
            self.update_url % identifier + ".hs%2Faggregations.json",
            data={"branch": branch, "content": metadata.json(indent=2), "commit_message": "some automated message"},
            params={
                "access_token": self.access_token,
            },
            timeout=15.0,
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = await self.get_metadata_repository(identifier, branch)

        return JSONResponse(json_metadata, status_code=201)

    @router.put('/metadata/gitlab/{identifier}', tags=["GitLab"])
    async def update_metadata(self, metadata: request_model_update, identifier, branch: str = "main") -> response_model:
        existing_metadata = await self.get_metadata_repository(identifier, branch)
        incoming_metadata = metadata.json(skip_defaults=True, exclude_unset=True)
        merged_metadata = {**existing_metadata, **json.loads(incoming_metadata)}
        response = requests.put(
            self.update_url % identifier + ".hs%2Faggregations.json",
            data={
                "branch": branch,
                "content": merged_metadata.json(indent=2),
                "commit_message": "some automated message",
            },
            params={
                "access_token": self.access_token,
            },
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return await self.get_metadata_repository(identifier, branch)

    async def _retrieve_metadata_from_repository(self, identifier, branch: str = "main"):
        def base64_decode(content):
            return str(base64.b64decode(content), "utf-8")

        response = requests.get(
            self.read_url % identifier + ".hs%2Faggregations.json" + f"?ref={branch}",
            params={"access_token": self.access_token},
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = json.loads(base64_decode(json.loads(response.text)["content"]))
        return json_metadata

    @router.get('/metadata/gitlab/{identifier}', tags=["GitLab"])
    async def get_metadata_repository(self, identifier, branch: str = "main") -> response_model:
        json_metadata = await self._retrieve_metadata_from_repository(identifier, branch)
        await self.submit(identifier=identifier, json_metadata=json_metadata)
        json_metadata["id"] = identifier
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

    @router.get('/files/gitlab/{identifier}', name="files_list", tags=["GitLab"])
    async def files_list(self, identifier: str, branch: str = "main"):
        def parse_listing(files_and_folders):
            files_list = []
            for f in files_and_folders:
                if f["type"] == "tree":
                    continue
                files_list.append(f)
            return files_list

        listfiles_url = 'https://gitlab.com/api/v4/projects/%s/repository/tree' % identifier
        response = requests.get(
            listfiles_url + f"?ref={branch}&recursive=true", params={"access_token": self.access_token}
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        files = parse_listing(response.json())
        return JSONResponse(files)

    @router.post('/files/gitlab/{identifier}/{file_identifier}', name="files_list", tags=["GitLab"])
    async def file_add(self, identifier: str, path: str = None, branch: str = "main"):
        raise NotImplementedError("")

    @router.put('/files/gitlab/{identifier}/{file_identifier}', name="files_list", tags=["GitLab"])
    async def file_move(self, identifier: str, file_identifier: str, path: str, branch: str = "main"):
        raise NotImplementedError("")

    @router.delete('/files/gitlab/{identifier}', name="files_list", tags=["GitLab"])
    async def file_delete(self, identifier: str, branch: str = "main"):
        raise NotImplementedError("")
