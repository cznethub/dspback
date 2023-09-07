import json

import requests
from fastapi import Request
from fastapi_restful.cbv import cbv
from fastapi_restful.inferring_router import InferringRouter
from hsmodels.schemas import ResourceMetadata as Res_MD
from hsmodels.schemas import rdf_string
from pydantic import BaseModel, create_model
from starlette.responses import JSONResponse

from dspback.database.procedures import delete_submission
from dspback.dependencies import RepositoryException
from dspback.pydantic_schemas import RepositoryType
from dspback.routers.metadata_class import MetadataRoutes, exists_and_is
from dspback.schemas.hydroshare.model import ResourceMetadata

router = InferringRouter()


def to_hydroshare_format(metadata_json):
    """
    Prepares form input for Storage in HydroShare by converting HydroShare profile urls to user IDs
    """

    def profile_url_to_user_id(user_json):
        if "profile_url" in user_json and user_json["profile_url"]:
            parts = user_json["profile_url"].strip('/').split('/')
            last_part = parts[-1]
            user_json["hydroshare_user_id"] = int(last_part)
            del user_json["profile_url"]
        return user_json

    if "creators" in metadata_json:
        for index in range(0, len(metadata_json["creators"])):
            metadata_json["creators"][index] = profile_url_to_user_id(metadata_json["creators"][index])
    if "contributors" in metadata_json:
        for index in range(0, len(metadata_json["contributors"])):
            metadata_json["contributors"][index] = profile_url_to_user_id(metadata_json["contributors"][index])
    return metadata_json


def from_hydroshare_format(metadata_json):
    """
    Reverses the to_hydroshare_format() function by:
     - converting HydroShare user IDs back to profile URLs
     - converting dictionaries to a list of dictionaries with key/value keys
    """

    def user_id_to_profile_url(user_json):
        if "hydroshare_user_id" in user_json:
            user_id = user_json["hydroshare_user_id"]
            profile_url = f"https://www.hydroshare.org/user/{user_id}/"
            user_json["profile_url"] = profile_url
            del user_json["hydroshare_user_id"]
        return user_json

    if "creators" in metadata_json:
        for index in range(0, len(metadata_json["creators"])):
            metadata_json["creators"][index] = user_id_to_profile_url(metadata_json["creators"][index])
    if "contributors" in metadata_json:
        for index in range(0, len(metadata_json["contributors"])):
            metadata_json["contributors"][index] = user_id_to_profile_url(metadata_json["contributors"][index])

    if "additional_metadata" in metadata_json:
        # TODO add the key/value list to the hsmodels schema.
        # add the response models back to the routes once hsmodels is updated.
        as_dict = metadata_json["additional_metadata"]
        metadata_json["additional_metadata"] = [{"key": key, "value": value} for key, value in as_dict.items()]

    return metadata_json


class HydroShareMetadataResponse(BaseModel):
    metadata: ResourceMetadata
    published: bool


@cbv(router)
class HydroShareMetadataRoutes(MetadataRoutes):
    request_model = ResourceMetadata
    response_model = HydroShareMetadataResponse
    repository_type = RepositoryType.HYDROSHARE

    @router.post(
        '/metadata/hydroshare',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["HydroShare"],
        summary="Create a HydroShare resource",
        description="Validates the incoming metadata, creates a new HydroShare resource and creates a submission record.",
    )
    async def create_metadata_repository(self, request: Request, metadata: request_model):
        access_token = await self.access_token(request)
        response = requests.post(
            self.create_url,
            params={"access_token": access_token},
            headers={"Content-Type": "application/json"},
            timeout=15.0,
        )

        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

        identifier = response.json()["resource_id"]
        # hydroshare doesn't accept all of the metadata on create, it also creates a creator with the user
        new_md = await self._retrieve_metadata_from_repository(request, identifier)
        metadata.creators = new_md["metadata"]["creators"] + metadata.creators
        metadata.citation = new_md["metadata"]["citation"]
        json_metadata = await self.update_metadata(request, metadata, identifier)

        return JSONResponse(json_metadata, status_code=201)

    @router.put(
        '/metadata/hydroshare/{identifier}',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["HydroShare"],
        summary="Update a HydroShare resource",
        description="Validates the incoming metadata and updates the HydroShare resource associated with the provided identifier.",
    )
    async def update_metadata(self, request: Request, metadata: request_model, identifier):
        access_token = await self.access_token(request)
        metadata_json = to_hydroshare_format(json.loads(metadata.json()))
        url = self.settings.hydroshare_view_url % identifier
        rdf = rdf_string(Res_MD(**metadata_json, identifier=url, url=url))
        response = requests.post(
            self.update_url % identifier,
            files={'file': ("resourcemetadata.xml", rdf)},
            params={"access_token": access_token},
        )

        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

        json_metadata = await self.submit(request, identifier)
        return json_metadata

    async def _retrieve_metadata_from_repository(self, request: Request, identifier):
        access_token = await self.access_token(request)
        response = requests.get(self.read_url % identifier, params={"access_token": access_token})
        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

        """
        HydroShare maintenance mode
          Parsing the response can fail if HydroShare is in maintenance mode.
          The request to HydroShare will return status code 200, but contain an HTML response.
        """
        try:
          json_metadata = json.loads(response.text)
        except:
          raise RepositoryException(status_code=500, detail="Failed to parse JSON response")
        
        json_metadata = json.loads(response.text)
        json_metadata = from_hydroshare_format(json_metadata)
        return self.wrap_metadata(json_metadata, exists_and_is("published", json_metadata))

    @router.get(
        '/metadata/hydroshare/{identifier}',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["HydroShare"],
        summary="Get a HydroShare resource",
        description="Retrieves the metadata for the HydroShare resource.",
    )  
    async def get_metadata_repository(self, request: Request, identifier):
        json_metadata = await self._retrieve_metadata_from_repository(request, identifier)
        await self.submit(request, identifier=identifier, json_metadata=json_metadata)
        return json_metadata
    
    @router.get(
        '/submission/hydroshare/{identifier}',
        tags=["HydroShare"],
        summary="Update and get a HydroShare resource Submission",
        description="Retrieves the metadata for the HydroShare resource and returns the updated Submission in the database.",
    )  
    async def update_and_get_submission(self, request: Request, identifier):
        await self.get_metadata_repository(request, identifier)
        return self.user.submission(identifier)

    @router.delete(
        '/metadata/hydroshare/{identifier}',
        tags=["HydroShare"],
        summary="Delete a HydroShare resource",
        description="Deletes the HydroShare resource along with the submission record.",
    )
    async def delete_metadata_repository(self, request: Request, identifier):
        await delete_submission(identifier, self.user)

        access_token = await self.access_token(request)
        response = requests.delete(self.delete_url % identifier, params={"access_token": access_token})

        if response.status_code >= 300:
            raise RepositoryException(status_code=response.status_code, detail=response.text)

    @router.put(
        '/submit/hydroshare/{identifier}',
        name="submit",
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["HydroShare"],
        summary="Register a HydroShare resource",
        description="Creates a submission record of the HydroShare resource.",
    )
    async def submit_repository_record(self, request: Request, identifier: str):
        json_metadata = await self.submit(request, identifier)
        return json_metadata

    @router.get(
        '/json/hydroshare/{identifier}',
        tags=["HydroShare"],
        summary="Get a HydroShare resource without validation",
        description="Retrieves the metadata for the HydroShare resource without validation.",
    )
    async def get_json_metadata_repository(self, request: Request, identifier):
        json_metadata = await self._retrieve_metadata_from_repository(request, identifier)
        return json_metadata
