import json
import uuid

from fastapi import Request
from fastapi_restful.cbv import cbv
from fastapi_restful.inferring_router import InferringRouter
from starlette.responses import JSONResponse

from dspback.database.procedures import delete_submission
from dspback.pydantic_schemas import RepositoryType
from dspback.routers.metadata_class import MetadataRoutes
from dspback.schemas.external.model import GenericDatasetSchemaForCzNetDataSubmissionPortalV100

router = InferringRouter()


@cbv(router)
class ExternalMetadataRoutes(MetadataRoutes):

    request_model = GenericDatasetSchemaForCzNetDataSubmissionPortalV100
    response_model = GenericDatasetSchemaForCzNetDataSubmissionPortalV100
    repository_type = RepositoryType.EXTERNAL

    @router.post(
        '/metadata/external',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["External"],
        summary="Create an external record",
        description="Create an external record along with the submission record.",
    )
    async def create_metadata_repository(self, request: Request, metadata: request_model):
        metadata.identifier = str(uuid.uuid4())
        metadata_json = json.loads(metadata.json())
        metadata_json = await self.submit(request, metadata.identifier, metadata_json)
        return JSONResponse(metadata_json, status_code=201)

    @router.put(
        '/metadata/external/{identifier}',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["External"],
        summary="Update an external record",
        description="update an external record along with the submission record.",
    )
    async def update_metadata(self, request: Request, metadata: request_model, identifier):
        return await self.submit(request, identifier, metadata.dict())

    @router.get(
        '/metadata/external/{identifier}',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["External"],
        summary="Get an external record",
        description="Get an external record along with the submission record.",
    )
    async def get_metadata_repository(self, identifier):
        submission = self.user.submission(identifier)
        metadata_json_str = submission.metadata_json
        metadata_json = json.loads(metadata_json_str)
        return metadata_json

    @router.delete(
        '/metadata/external/{identifier}',
        tags=["External"],
        summary="Delete an external record",
        description="Deletes an external record.",
    )
    async def delete_metadata_repository(self, identifier):
        await delete_submission(identifier, self.user)
