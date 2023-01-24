import json
import os
import tempfile
import uuid

from fastapi import Request
from fastapi_restful.cbv import cbv
from fastapi_restful.inferring_router import InferringRouter
from minio import Minio
from starlette.responses import JSONResponse

from dspback.pydantic_schemas import RepositoryType
from dspback.routers.metadata_class import MetadataRoutes
from dspback.schemas.hydroshare.model import ResourceMetadata

router = InferringRouter()


@cbv(router)
class HydroShareMinioMetadataRoutes(MetadataRoutes):

    request_model = ResourceMetadata
    response_model = ResourceMetadata
    repository_type = RepositoryType.HYDROSHARE

    @staticmethod
    def minio_client() -> Minio:
        return Minio(
            "minio.cuahsi.io",
            access_key="lMS3BQuA6VmViGjQ",
            secret_key="obKYT3yaYfJqsbqlzJ6nM2ws7xZUWNhK",
        )

    def write_metadata(self, metadata_json: str, identifier: str = None) -> str:
        client = self.minio_client()
        client.get_presigned_url()
        if not identifier:
            identifier = str(uuid.uuid4())
            client.make_bucket(identifier)
        with tempfile.TemporaryDirectory() as tmpdirname:
            local_temp_file = os.path.join(tmpdirname, 'temp.txt')
            fp = open(local_temp_file, 'w')
            fp.write(metadata_json)
            fp.close()
            client.fput_object(identifier, "metadata.json", local_temp_file)
        return identifier


    @router.post(
        '/metadata/hydroshare',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["HydroShare"],
        summary="Create a HydroShare minio resource",
        description="Validates the incoming metadata, creates a new HydroShare minio resource and creates a submission record.",
    )
    async def create_metadata_repository(self, request: Request, metadata: request_model):
        # access_token = self.access_token(request)
        metadata_json = json.loads(metadata.json())
        identifier = self.write_metadata(metadata_json)
        metadata_json = await self.submit(request, identifier, metadata_json)
        return JSONResponse(metadata_json, status_code=201)

    @router.put(
        '/metadata/hydroshare/{identifier}',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["HydroShare"],
        summary="Update a HydroShare resource",
        description="Validates the incoming metadata and updates the HydroShare resource associated with the provided identifier.",
    )
    async def update_metadata(self, request: Request, metadata: request_model, identifier):
        metadata_json = json.loads(metadata.json())
        identifier = self.write_metadata(metadata_json)
        json_metadata = await self.submit(request, identifier)
        return json_metadata

    async def _retrieve_metadata_from_repository(self, request: Request, identifier):
        with tempfile.TemporaryDirectory() as tmpdirname:
            local_temp_file = os.path.join(tmpdirname, 'test.txt')
            self.minio_client().fget_object(identifier, "metadata.json", local_temp_file)
            with open(local_temp_file, 'r') as f:
                return json.loads(f.read())

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

    @router.delete(
        '/metadata/hydroshare/{identifier}',
        tags=["HydroShare"],
        summary="Delete a HydroShare resource",
        description="Deletes the HydroShare resource along with the submission record.",
    )
    async def delete_metadata_repository(self, request: Request, identifier):
        self.minio_client().remove_object(identifier, "metadata.json")

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

    @router.get(
        '/json/hydroshare/{identifier}',
        tags=["HydroShare"],
        summary="Get a HydroShare resource without validation",
        description="Retrieves the metadata for the HydroShare resource without validation.",
    )
    async def get_json_metadata_repository(self, request: Request, identifier):
        json_metadata = await self._retrieve_metadata_from_repository(request, identifier)
        return json_metadata
