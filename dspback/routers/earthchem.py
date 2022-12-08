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


def prepare_metadata_for_ecl(json_metadata):
    # join leadAuthor and contributors
    if "leadAuthor" in json_metadata:
        lead_author = json_metadata["leadAuthor"]
        del json_metadata["leadAuthor"]
        contributors = json_metadata.get("contributors", [])
        contributors.insert(0, lead_author)
        json_metadata["contributors"] = contributors
    return json_metadata


@cbv(router)
class EarthChemMetadataRoutes(MetadataRoutes):

    request_model = Record
    request_model_update = Record
    response_model = Record
    repository_type = RepositoryType.EARTHCHEM

    @router.post(
        '/metadata/earthchem',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["EarthChem"],
        summary="Create an EarthChem record",
        description="Validates the incoming metadata, creates a new EarthChem record and creates a submission record.",
    )
    async def create_metadata_repository(self, request: Request, metadata: request_model) -> response_model:
        access_token = await self.access_token(request)
        json_metadata = prepare_metadata_for_ecl(json.loads(metadata.json(exclude_none=True)))
        response = requests.post(
            self.create_url,
            json=json_metadata,
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
        json_metadata = await self.get_metadata_repository(request, identifier)

        return JSONResponse(json_metadata, status_code=201)

    @router.put(
        '/metadata/earthchem/{identifier}',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["EarthChem"],
        summary="Update an EarthChem record",
        description="Validates the incoming metadata and updates the EarthChem resource associated with the provided identifier.",
    )
    async def update_metadata(self, request: Request, metadata: request_model_update, identifier) -> response_model:
        existing_metadata = await self.get_metadata_repository(request, identifier)
        incoming_metadata = metadata.json(skip_defaults=True, exclude_unset=True)
        json_metadata = json.loads(incoming_metadata)

        merged_metadata = {**existing_metadata, **json_metadata}
        merged_metadata = prepare_metadata_for_ecl(merged_metadata)

        access_token = await self.access_token(request)
        response = requests.put(
            self.update_url % identifier,
            json=merged_metadata,
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + str(access_token)},
        )

        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

        return await self.get_metadata_repository(request, identifier)

    async def _retrieve_metadata_from_repository(self, request: Request, identifier):
        access_token = await self.access_token(request)
        response = requests.get(
            self.read_url % identifier,
            headers={"accept": "application/json", "Authorization": "Bearer " + str(access_token)},
        )

        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

        # split first contributors to leadAuthor
        json_metadata = json.loads(response.text)
        if "contributors" in json_metadata:
            all_contributors = json_metadata["contributors"]
            for contributor in json_metadata["contributors"]:
                if contributor["identifiers"] is None:
                    contributor["identifiers"] = []
            if len(all_contributors) > 0:
                lead_author = all_contributors.pop(0)
                json_metadata["leadAuthor"] = lead_author
                json_metadata["contributors"] = all_contributors

        return json_metadata

    @router.get(
        '/metadata/earthchem/{identifier}',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["EarthChem"],
        summary="Get an EarthChem record",
        description="Retrieves the metadata for the EarthChem record.",
    )
    async def get_metadata_repository(self, request: Request, identifier) -> response_model:
        json_metadata = await self._retrieve_metadata_from_repository(request, identifier)
        await self.submit(request, identifier=identifier, json_metadata=json_metadata)
        return json_metadata

    @router.delete(
        '/metadata/earthchem/{identifier}',
        tags=["EarthChem"],
        summary="Delete an EarthChem record",
        description="Deletes the EarthChem record along with the submission record.",
    )
    async def delete_metadata_repository(self, request: Request, identifier):
        delete_submission(self.db, self.repository_type, identifier, self.user)

        access_token = await self.access_token(request)
        response = requests.delete(
            self.delete_url % str(identifier),
            headers={"accept": "application/json", "Authorization": "Bearer " + str(access_token)},
        )
        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

    @router.put(
        '/submit/earthchem/{identifier}',
        name="submit",
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["EarthChem"],
        summary="Register an EarthChem record",
        description="Creates a submission record of the EarthChem record.",
    )
    async def submit_repository_record(self, identifier: str):
        json_metadata = await self.submit(identifier)
        return json_metadata

    @router.get(
        '/json/earthchem/{identifier}',
        tags=["EarthChem"],
        summary="Get an EarthChem record without validation",
        description="Retrieves the metadata for the EarthChem record without validation.",
    )
    async def get_json_metadata_repository(self, request: Request, identifier) -> response_model:
        json_metadata = await self._retrieve_metadata_from_repository(request, identifier)
        return json_metadata
