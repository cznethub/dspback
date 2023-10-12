import json

import requests
from fastapi import Request
from fastapi_restful.cbv import cbv
from fastapi_restful.inferring_router import InferringRouter
from pydantic import BaseModel
from starlette.responses import JSONResponse

from dspback.database.procedures import delete_submission
from dspback.dependencies import RepositoryException
from dspback.pydantic_schemas import RepositoryType, Submission
from dspback.routers.metadata_class import MetadataRoutes, exists_and_is
from dspback.schemas.zenodo.model import ZenodoDatasetsSchemaForCzNetV100

router = InferringRouter()


def to_zenodo_format(metadata_json):
    """
    Prepares form input for Storage in Zenodo.  Notes is a string field we are using to store required funding
    information. Our forms only use properties within the metadata property.
    """

    metadata_json = {"metadata": metadata_json}
    return metadata_json


def from_zenodo_format(json_metadata):
    """
    Prepares Zenodo storage for our forms.  Notes is a string field we are using to store required funding
    information. Our forms only use properties within the metadata property.
    """
    json_metadata["metadata"] = json_metadata["metadata"]["metadata"]
    return json_metadata


class ZenodoMetadataResponse(BaseModel):
    metadata: ZenodoDatasetsSchemaForCzNetV100
    published: bool


@cbv(router)
class ZenodoMetadataRoutes(MetadataRoutes):
    request_model = ZenodoDatasetsSchemaForCzNetV100
    response_model = ZenodoMetadataResponse
    repository_type = RepositoryType.ZENODO

    @router.post(
        '/metadata/zenodo',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["Zenodo"],
        summary="Create a Zenodo resource",
        description="Validates the incoming metadata, creates a new Zenodo record and creates a submission record.",
    )
    async def create_metadata_repository(self, request: Request, metadata: request_model):
        metadata_json = json.loads(metadata.json(exclude_none=True))
        metadata_json = to_zenodo_format(metadata_json)
        access_token = await self.access_token(request)
        response = requests.post(
            self.create_url,
            json=metadata_json,
            params={"access_token": access_token},
            headers={"Content-Type": "application/json"},
            timeout=15.0,
        )

        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

        identifier = response.json()["record_id"]
        json_metadata = await self.get_metadata_repository(request, identifier)

        return JSONResponse(json_metadata, status_code=201)

    @router.put(
        '/metadata/zenodo/{identifier}',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["Zenodo"],
        summary="Update a Zenodo record",
        description="Validates the incoming metadata and updates the Zenodo record associated with the provided identifier.",
    )
    async def update_metadata(self, request: Request, metadata: request_model, identifier):
        incoming_metadata = metadata.json(skip_defaults=True, exclude_unset=True)
        zenodo_metadata = to_zenodo_format(json.loads(incoming_metadata))
        access_token = await self.access_token(request)
        response = requests.put(
            self.update_url % identifier,
            json=zenodo_metadata,
            headers={"Content-Type": "application/json"},
            params={"access_token": access_token},
        )

        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

        return await self.get_metadata_repository(request, identifier)

    async def _retrieve_metadata_from_repository(self, request: Request, identifier):
        access_token = await self.access_token(request)
        response = requests.get(self.read_url % identifier, params={"access_token": access_token})

        if response.status_code >= 300:
            response = requests.get(
                self.settings.zenodo_published_read_url % identifier, params={"access_token": access_token}
            )

        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

        json_metadata = json.loads(response.text)
        return self.wrap_metadata(json_metadata, exists_and_is("publication_date", json_metadata["metadata"]))

    @router.get(
        '/metadata/zenodo/{identifier}',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["Zenodo"],
        summary="Get a Zenodo record",
        description="Retrieves the metadata for the Zenodo record.",
    )
    async def get_metadata_repository(self, request: Request, identifier):
        json_metadata = await self._retrieve_metadata_from_repository(request, identifier)
        await self.submit(request, identifier=identifier, json_metadata=json_metadata)
        json_metadata = from_zenodo_format(json_metadata)

        return json_metadata

    @router.get(
        '/submission/zenodo/{identifier}',
        tags=["Zenodo"],
        summary="Update and get a Zenodo record Submission",
        description="Retrieves the metadata for the Zenodo record and returns the updated Submission in the database.",
    )
    async def update_and_get_submission(self, request: Request, identifier):
        await self.get_metadata_repository(request, identifier)
        return self.user.submission(identifier)

    @router.delete(
        '/metadata/zenodo/{identifier}',
        tags=["Zenodo"],
        summary="Delete a Zenodo record",
        description="Deletes the Zenodo record along with the submission record.",
    )
    async def delete_metadata_repository(self, request: Request, identifier):
        await delete_submission(identifier, self.user)

        access_token = await self.access_token(request)
        response = requests.delete(self.delete_url % identifier, params={"access_token": access_token})
        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

    @router.put(
        '/submit/zenodo/{identifier}',
        name="submit",
        response_model=Submission,
        tags=["Zenodo"],
        summary="Register a Zenodo record",
        description="Creates a submission record of the Zenodo record.",
    )
    async def submit_repository_record(self, request: Request, identifier: str):
        json_metadata = await self.submit(request, identifier)
        return json_metadata["metadata"]

    @router.get(
        '/json/zenodo/{identifier}',
        tags=["Zenodo"],
        summary="Get a Zenodo record without validation",
        description="Retrieves the metadata for the Zenodo record without validation.",
    )
    async def get_json_metadata_repository(self, request: Request, identifier):
        json_metadata = await self._retrieve_metadata_from_repository(request, identifier)
        json_metadata = from_zenodo_format(json_metadata)

        return json_metadata
