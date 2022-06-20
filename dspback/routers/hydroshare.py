import json

import requests
from fastapi import HTTPException, Request
from fastapi_restful.cbv import cbv
from fastapi_restful.inferring_router import InferringRouter
from starlette.responses import JSONResponse

from dspback.database.procedures import delete_submission
from dspback.pydantic_schemas import RepositoryType, SubmissionBase
from dspback.routers.metadata_class import MetadataRoutes
from dspback.schemas.hydroshare.model import ResourceMetadata

router = InferringRouter()


@cbv(router)
class HydroShareMetadataRoutes(MetadataRoutes):

    request_model = ResourceMetadata
    response_model = ResourceMetadata
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
            raise HTTPException(status_code=response.status_code, detail=response.text)

        identifier = response.json()["resource_id"]
        # hydroshare doesn't accept all of the metadata on create
        json_metadata = await self.update_metadata(metadata, identifier)

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
        from dspback.schemas.hydroshare.model import License

        if isinstance(metadata.rights, License):
            metadata.rights = metadata.rights.as_rights()
        access_token = await self.access_token(request)
        response = requests.put(
            self.update_url % identifier,
            data=metadata.json(skip_defaults=True),
            headers={"Content-Type": "application/json"},
            params={"access_token": access_token},
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = await self.submit(identifier)
        return json_metadata

    async def _retrieve_metadata_from_repository(self, request: Request, identifier):
        access_token = await self.access_token(request)
        response = requests.get(self.read_url % identifier, params={"access_token": access_token})
        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = json.loads(response.text)
        if "additional_metadata" in json_metadata:
            # TODO add the key/value list to the hsmodels schema.
            # add the response models back to the routes once hsmodels is updated.
            as_dict = json_metadata["additional_metadata"]
            json_metadata["additional_metadata"] = [{"key": key, "value": value} for key, value in as_dict.items()]
        if "rights" in json_metadata:
            rights = json_metadata["rights"]
            if "statement" in rights:
                from dspback.schemas.hydroshare.model import License

                license = License.from_statement(rights["statement"])
                if license:
                    json_metadata["rights"] = {"license": license}
        return json_metadata

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
        await self.submit(identifier=identifier, json_metadata=json_metadata)
        return json_metadata

    @router.delete(
        '/metadata/hydroshare/{identifier}',
        tags=["HydroShare"],
        summary="Delete a HydroShare resource",
        description="Deletes the HydroShare resource along with the submission record.",
    )
    async def delete_metadata_repository(self, request: Request, identifier):
        delete_submission(self.db, self.repository_type, identifier, self.user)

        access_token = await self.access_token(request)
        response = requests.delete(self.delete_url % identifier, params={"access_token": access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    @router.put(
        '/submit/hydroshare/{identifier}',
        name="submit",
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["HydroShare"],
        summary="Register a HydroShare resource",
        description="Creates a submission record of the HydroShare resource.",
    )
    async def submit_repository_record(self, identifier: str):
        json_metadata = await self.submit(identifier)
        return json_metadata
