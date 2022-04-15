import base64
import json
import uuid

import requests
from fastapi import APIRouter, HTTPException, UploadFile
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

    async def _write_metadata(self, identifier, branch, metadata, aggregation_identifier):
        all_metadata = await self._retrieve_metadata_from_repository(identifier, branch)
        if aggregation_identifier in all_metadata:
            existing_metadata = all_metadata[aggregation_identifier]
            incoming_metadata = metadata.json(skip_defaults=True, exclude_unset=True)
            merged_metadata = {**existing_metadata, **json.loads(incoming_metadata)}
        else:
            merged_metadata = metadata
        all_metadata[str(aggregation_identifier)] = json.loads(merged_metadata.json())
        as_json = json.dumps(all_metadata)
        response = requests.put(
            self.update_url % identifier + ".hs%2Faggregations.json",
            data={
                "branch": branch,
                "content": as_json,
                "commit_message": "some automated message",
            },
            params={
                "access_token": self.access_token,
            },
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

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

            identifier = response.json()["id"]

            if response.status_code >= 300:
                raise HTTPException(status_code=response.status_code, detail=response.text)

            response = requests.post(
                self.update_url % identifier + ".hs%2Faggregations.json",
                data={"branch": branch, "content": "{}", "commit_message": "some automated message"},
                params={
                    "access_token": self.access_token,
                },
                timeout=15.0,
            )

        return await self.create_metadata_aggregation(metadata, identifier, branch)

    @router.post('/metadata/gitlab/{identifier}', tags=["GitLab"])
    async def create_metadata_aggregation(
        self, metadata: request_model, identifier=None, branch: str = "main"
    ) -> response_model:

        aggregation_identifier = uuid.uuid4()
        await self._write_metadata(identifier, branch, metadata, aggregation_identifier)

        json_metadata = await self.get_aggregation_metadata_repository(identifier, aggregation_identifier, branch)

        return JSONResponse(json_metadata, status_code=201)

    @router.put('/metadata/gitlab/{identifier}', tags=["GitLab"])
    async def update_metadata(
        self, metadata: request_model_update, identifier, aggregation_identifier: str = None, branch: str = "main"
    ) -> response_model:
        existing_metadata = await self.get_aggregation_metadata_repository(identifier, branch)
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

    async def _retrieve_metadata_from_repository(self, identifier, branch: str):
        def base64_decode(content):
            return str(base64.b64decode(content), "utf-8")

        response = requests.get(
            self.read_url % identifier + ".hs%2Faggregations.json" + f"?ref={branch}",
            params={"access_token": self.access_token},
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        response_json = response.json()
        decoded_content = base64_decode(response_json["content"])
        json_metadata = json.loads(decoded_content)
        # TOOO, won't be able to do this soon
        agg_metadata = list(json_metadata.values())
        submission_json_metadata = {}
        if len(agg_metadata) > 0:
            submission_json_metadata = list(json_metadata.values())[0]
            await self.submit(identifier=identifier, json_metadata=submission_json_metadata)
        return submission_json_metadata

    @router.get('/metadata/gitlab/{identifier}', tags=["GitLab"])
    async def get_aggregation_metadata_repository(
        self, identifier, aggregation_identifier: str = None, branch: str = "main"
    ) -> response_model:
        json_metadata = await self._retrieve_metadata_from_repository(identifier, branch)
        # aggregation_metadata = json_metadata[aggregation_identifier]
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

    def _hs_files(self, identifier: str, branch: str):
        _, _, hs_files = self._all_files(identifier, branch)
        return hs_files

    def _files(self, identifier: str, branch: str):
        files, folders, _ = self._all_files(identifier, branch)
        return files, folders

    def _all_files(self, identifier: str, branch: str):

        listfiles_url = 'https://gitlab.com/api/v4/projects/%s/repository/tree' % identifier
        response = requests.get(
            listfiles_url + f"?ref={branch}&recursive=true", params={"access_token": self.access_token}
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        files = []
        hs_files = []
        folders = []
        for file in response.json():
            if file["type"] == "tree":
                if file["name"] != ".hs":
                    folders.append(file)
            elif file["path"].startswith(".hs/"):
                hs_files.append(file)
            else:
                files.append(file)
        return files, folders, hs_files

    @router.get('/files/gitlab/{identifier}', name="files_list", tags=["GitLab"])
    async def files_list(self, identifier: str, path: str, branch: str = "main"):
        files, folders = self._files(identifier, branch)

        files_in_folder = []
        for f in files:
            if f["path"].startswith(path):
                if not path:
                    if f["name"] == f["path"]:
                        files_in_folder.append(f)
                else:
                    files_in_folder.append(f)
        folders_in_folder = []
        for f in folders:
            if f["path"].startswith(path) and f["path"] != path:
                folders_in_folder.append(f)

        return JSONResponse({"files": files_in_folder, "folders": folders_in_folder})

    @router.post('/files/gitlab/{identifier}', name="file_add", tags=["GitLab"])
    async def file_add(
        self, identifier: str, file: UploadFile, aggregation: str = None, path: str = None, branch: str = "main"
    ):

        response = requests.post(
            self.update_url % identifier + file.filename,
            data={"branch": branch, "content": await file.read(), "commit_message": "some automated message"},
            params={
                "access_token": self.access_token,
            },
            timeout=15.0,
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    @router.put('/files/gitlab/{identifier}/{file_identifier}', name="file_add", tags=["GitLab"])
    async def file_update(
        self,
        identifier: str,
        file_identifier: str,
        file: UploadFile,
        aggregation: str = None,
        path: str = None,
        branch: str = "main",
    ):
        files, _, _ = self._files(identifier, branch)
        f = next(f for f in files if f.id == file_identifier)
        response = requests.put(
            self.update_url % identifier + f.path,
            data={"branch": branch, "content": await file.read(), "commit_message": "some automated message"},
            params={
                "access_token": self.access_token,
            },
            timeout=15.0,
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response
