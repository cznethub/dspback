import json

import requests
from fastapi import HTTPException, Request
from fastapi_restful.cbv import cbv
from fastapi_restful.inferring_router import InferringRouter
from starlette.responses import JSONResponse

from dspback.database.procedures import delete_submission
from dspback.pydantic_schemas import RepositoryType, SubmissionBase
from dspback.routers.metadata_class import MetadataRoutes
from dspback.schemas.zenodo.model import Notes, ZenodoDatasetsSchemaForCzNetV100

router = InferringRouter()


def to_notes_format(notes_json):
    notes = Notes(**notes_json)
    notes_string = ""
    if notes.funding_agency_name:
        notes_string += f"Funding Agency Name: {notes.funding_agency_name}"
        notes_string += "\n"
    if notes.award_title:
        notes_string += f"Award Title: {notes.award_title}"
        notes_string += "\n"
    if notes.award_number:
        notes_string += f"Award Number: {notes.award_number}"
        notes_string += "\n"
    if notes.funding_agency_url:
        notes_string += f"Funding Agency URL: {notes.funding_agency_url}"
    return notes_string


def to_zenodo_format(metadata_json):
    """
    Prepares form input for Storage in Zenodo.  Notes is a string field we are using to store required funding
    information. Our forms only use properties within the metadata property.
    """

    metadata_json["notes"] = to_notes_format(metadata_json["notes"])
    metadata_json = {"metadata": metadata_json}
    return metadata_json


def from_notes_format(notes_string):
    notes_lines = notes_string.split("\n")

    funding_agency_name = None
    award_title = None
    award_number = None
    funding_agency_url = None
    for line in notes_lines:
        if "Funding Agency Name: " in line:
            funding_agency_name = line.split(": ")[1]
        if "Award Title: " in line:
            award_title = line.split(": ")[1]
        if "Award Number: " in line:
            award_number = line.split(": ")[1]
        if "Funding Agency URL: " in line:
            funding_agency_url = line.split(": ")[1]
    notes_json = {
        "funding_agency_name": funding_agency_name,
        "award_title": award_title,
        "award_number": award_number,
        "funding_agency_url": funding_agency_url,
    }
    return notes_json


def from_zenodo_format(json_metadata):
    """
    Prepares Zenodo storage for our forms.  Notes is a string field we are using to store required funding
    information. Our forms only use properties within the metadata property.
    """
    json_metadata = json_metadata["metadata"]
    if "notes" in json_metadata:
        json_metadata["notes"] = from_notes_format(json_metadata["notes"])
    return json_metadata


@cbv(router)
class ZenodoMetadataRoutes(MetadataRoutes):

    request_model = ZenodoDatasetsSchemaForCzNetV100
    response_model = ZenodoDatasetsSchemaForCzNetV100
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
            raise HTTPException(status_code=response.status_code, detail=response.text)

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
        existing_metadata = await self.get_metadata_repository(request, identifier)
        incoming_metadata = metadata.json(skip_defaults=True, exclude_unset=True)
        merged_metadata = {**existing_metadata, **json.loads(incoming_metadata)}
        merged_metadata = to_zenodo_format(merged_metadata)
        access_token = await self.access_token(request)
        response = requests.put(
            self.update_url % identifier,
            json=merged_metadata,
            headers={"Content-Type": "application/json"},
            params={"access_token": access_token},
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        # await self.submit(identifier)
        return await self.get_metadata_repository(request, identifier)

    async def _retrieve_metadata_from_repository(self, request: Request, identifier):
        access_token = await self.access_token(request)
        response = requests.get(self.read_url % identifier, params={"access_token": access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = json.loads(response.text)
        return json_metadata

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

    @router.delete(
        '/metadata/zenodo/{identifier}',
        tags=["Zenodo"],
        summary="Delete a Zenodo record",
        description="Deletes the Zenodo record along with the submission record.",
    )
    async def delete_metadata_repository(self, request: Request, identifier):
        delete_submission(self.db, self.repository_type, identifier, self.user)
        access_token = await self.access_token(request)
        response = requests.delete(self.delete_url % identifier, params={"access_token": access_token})
        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    @router.put(
        '/submit/zenodo/{identifier}',
        name="submit",
        response_model=SubmissionBase,
        tags=["Zenodo"],
        summary="Register a Zenodo record",
        description="Creates a submission record of the Zenodo record.",
    )
    async def submit_repository_record(self, identifier: str):
        json_metadata = await self.submit(identifier)
        return json_metadata["metadata"]
