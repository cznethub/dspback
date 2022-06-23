import json

import requests
from fastapi import Request
from fastapi_restful.cbv import cbv
from fastapi_restful.inferring_router import InferringRouter
from starlette.responses import JSONResponse

from dspback.database.procedures import delete_submission
from dspback.dependencies import RepositoryException
from dspback.pydantic_schemas import RepositoryType
from dspback.routers.metadata_class import MetadataRoutes
from dspback.schemas.earthchem.model import Record

router = InferringRouter()


@cbv(router)
class EarthChemMetadataRoutes(MetadataRoutes):

    request_model = Record
    request_model_update = Record
    response_model = Record
    repository_type = RepositoryType.EARTHCHEM

    @router.post('/metadata/earthchem', tags=["EarthChem"])
    async def create_metadata_repository(self, request: Request, metadata: request_model) -> response_model:
        access_token = await self.access_token(request)
        response = requests.post(
            self.create_url,
            json=json.loads(metadata.json(exclude_none=True)),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + str(access_token),
                "accept": "application/json",
            },
            timeout=15.0,
        )

        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

        identifier = response.json()["id"]
        json_metadata = await self.update_metadata(request, metadata, identifier)

        return JSONResponse(json_metadata, status_code=201)

    @router.put('/metadata/earthchem/{identifier}', tags=["EarthChem"])
    async def update_metadata(self, request: Request, metadata: request_model_update, identifier) -> response_model:
        existing_metadata = await self.get_metadata_repository(request, identifier)
        incoming_metadata = metadata.json(skip_defaults=True, exclude_unset=True)
        json_metadata = json.loads(incoming_metadata)

        merged_metadata = {**existing_metadata, **json_metadata}
        # join leadAuthor and creators
        if "leadAuthor" in merged_metadata:
            lead_author = merged_metadata["leadAuthor"]
            del merged_metadata["leadAuthor"]
            creators = merged_metadata["creators"]
            creators.insert(0, lead_author)
            merged_metadata["creators"] = creators

        access_token = await self.access_token(request)
        response = requests.put(
            self.update_url % identifier,
            json=merged_metadata,
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + str(access_token)},
        )

        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

        # await self.submit(identifier)
        return await self.get_metadata_repository(request, identifier)

    async def _retrieve_metadata_from_repository(self, request: Request, identifier):
        access_token = await self.access_token(request)
        response = requests.get(
            self.read_url % identifier,
            headers={"accept": "application/json", "Authorization": "Bearer " + str(access_token)},
        )

        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

        # split first creator to leadAuthor
        json_metadata = json.loads(response.text)
        if "creators" in json_metadata:
            all_creators = json_metadata["creators"]
            if len(all_creators) > 0:
                lead_author = all_creators.pop(0)
                json_metadata["leadAuthor"] = lead_author
                json_metadata["creators"] = all_creators

        return json_metadata

    @router.get('/metadata/earthchem/{identifier}', tags=["EarthChem"])
    async def get_metadata_repository(self, request: Request, identifier) -> response_model:
        json_metadata = await self._retrieve_metadata_from_repository(request, identifier)
        await self.submit(request, identifier=identifier, json_metadata=json_metadata)
        return json_metadata

    @router.delete('/metadata/earthchem/{identifier}', tags=["EarthChem"])
    async def delete_metadata_repository(self, request: Request, identifier):
        access_token = await self.access_token(request)
        response = requests.delete(
            self.delete_url % str(identifier),
            headers={"accept": "application/json", "Authorization": "Bearer " + str(access_token)},
        )
        if response.status_code == 403:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

        delete_submission(self.db, self.repository_type, identifier, self.user)

    @router.put('/submit/earthchem/{identifier}', name="submit", tags=["EarthChem"])
    async def submit_repository_record(self, identifier: str):
        json_metadata = await self.submit(identifier)
        return json_metadata
