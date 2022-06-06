import json
import uuid

from fastapi import Depends, HTTPException
from fastapi_restful.cbv import cbv
from fastapi_restful.inferring_router import InferringRouter
from minio import Minio
from requests import Session
from starlette.responses import JSONResponse

from dspback.config import repository_config
from dspback.database.models import RepositoryTokenTable, UserTable
from dspback.database.procedures import delete_submission
from dspback.dependencies import get_current_user, get_db
from dspback.pydantic_schemas import RepositoryType
from dspback.routers.submissions import submit_record
from dspback.schemas.external.model import GenericDatasetSchemaForCzNetDataSubmissionPortalV100
from dspback.schemas.hydroshare.model import ResourceMetadata

router = InferringRouter()


class MetadataRoutes:
    db: Session = Depends(get_db)
    user: UserTable = Depends(get_current_user)

    request_model = None
    response_model = None
    repository_type = None

    @property
    def access_token(self):
        repository_token: RepositoryTokenTable = self.user.repository_token(self.db, self.repository_type)
        if not repository_token:
            raise HTTPException(
                status_code=403, detail=f"User has not authorized permissions with {self.repository_type}"
            )
        return repository_token.access_token

    async def submit(self, identifier, json_metadata=None):
        if json_metadata is None:
            json_metadata = await self._retrieve_metadata_from_repository(identifier)
        submit_record(self.db, self.repository_type, identifier, self.user, json_metadata)
        return json_metadata

    def __init__(self):
        if self.request_model is None:
            raise ValueError("field request_model must be defined on the child class")
        if self.response_model is None:
            raise ValueError("field response_model must be defined on the child class")
        if self.repository_type is None:
            raise ValueError("field repository_name must be defined on the child class")

        if self.repository_type not in repository_config:
            raise ValueError(f"No configuration found for {self.repository_type}")

        if "read" not in repository_config[self.repository_type]:
            raise ValueError(f"No 'read' value found for {self.repository_type} configuration")
        self.read_url = repository_config[self.repository_type]["read"]

        if "create" not in repository_config[self.repository_type]:
            raise ValueError(f"No 'create' value found for {self.repository_type} configuration")
        self.create_url = repository_config[self.repository_type]["create"]

        if "update" not in repository_config[self.repository_type]:
            raise ValueError(f"No 'update' value found for {self.repository_type} configuration")
        self.update_url = repository_config[self.repository_type]["update"]

        if "delete" not in repository_config[self.repository_type]:
            raise ValueError(f"No 'delete' value found for {self.repository_type} configuration")
        self.delete_url = repository_config[self.repository_type]["delete"]


def parse_aggregations_and_files(agg, agg_dict, files_dict, id):
    md = agg.metadata.dict()
    if "additional_metadata" in md:
        # TODO add the key/value list to the hsmodels schema.
        # add the response models back to the routes once hsmodels is updated.
        as_dict = md["additional_metadata"]
        md["additional_metadata"] = [{"key": key, "value": value} for key, value in as_dict.items()]

    files = {}
    for file in agg.files():
        file_id = str(uuid.uuid4())
        files[file_id] = {"path": file.path, "checksum": file.checksum}
    md["files"] = list(files.keys())
    files_dict.update(files)

    aggs = []
    for agg in agg.aggregations():
        uid = str(uuid.uuid4())
        aggs.append(uid)
        agg_dict, files = parse_aggregations_and_files(agg, agg_dict, files_dict, uid)

    md["aggregations"] = list(aggs)
    agg_dict[id] = md
    return agg_dict, files_dict


mem_db = {}


@cbv(router)
class HydroShareMetadataRoutes(MetadataRoutes):
    request_model = ResourceMetadata
    response_model = ResourceMetadata
    repository_type = RepositoryType.HYDROSHARE

    async def _retrieve_metadata_from_repository(self, identifier):
        from hsclient import HydroShare
        from dspback.config import Settings, get_settings
        settings: Settings = get_settings()
        hs = HydroShare(host="beta.hydroshare.org", client_id=settings.hydroshare_client_id, token={"access_token": self.access_token, "token_type": "Bearer"})
        res = hs.resource(resource_id=identifier)
        aggregations, files = parse_aggregations_and_files(res, {}, {}, identifier)

        # resolve files first
        for agg in aggregations.values():
            resolved_files = []
            for file_id in agg["files"]:
                files[file_id]["id"] = file_id
                resolved_files.append(files[file_id])
            agg["files"] = resolved_files

        # add aggregation_id

        for key, agg in aggregations.items():
            resolved_aggregations = []
            for agg_id in agg["aggregations"]:
                aggregations[agg_id]["id"] = agg_id
                resolved_aggregations.append(aggregations[agg_id])
            agg["aggregations"] = resolved_aggregations

        for agg_id, agg in aggregations.items():
            mem_db[agg_id] = agg

    @router.get(
        '/metadata/hydroshare/{identifier}',
        tags=["HydroShare"],
        summary="Get a HydroShare resource",
        description="Retrieves the metadata for the HydroShare resource.",
    )
    async def get_metadata_repository(self, identifier):
        if identifier not in mem_db:
            await self._retrieve_metadata_from_repository(identifier)
        return mem_db[identifier]

    @router.get(
        '/metadata/hydroshare',
        tags=["HydroShare"],
        summary="Get a HydroShare my-resource",
        description="Retrieves the metadata for the HydroShare resource.",
    )
    async def get_my_resources(self):
        from hsclient import HydroShare
        from dspback.config import Settings, get_settings
        settings: Settings = get_settings()
        hs = HydroShare(host="beta.hydroshare.org", client_id=settings.hydroshare_client_id, token={"access_token": self.access_token, "token_type": "Bearer"})
        user_info = hs.my_user_info()
        user_id = user_info["email"]
        my_resources = [res for res in hs.search(owner=user_id)]
        return my_resources


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
    async def create_metadata_repository(self, metadata: request_model):
        metadata.identifier = str(uuid.uuid4())
        metadata_json = json.loads(metadata.json())
        client = Minio(
            "play.min.io",
            access_key="Q3AM3UQ867SPQQA43P2F",
            secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
        )
        client.make_bucket(metadata.identifier)
        fp = open('test.txt', 'w')
        fp.write(metadata.json(indent=2))
        fp.close()
        client.fput_object(metadata.identifier, ".hs/aggregations.json", 'test.txt')
        metadata_json = await self.submit(metadata.identifier, metadata_json)
        return JSONResponse(metadata_json, status_code=201)

    @router.put(
        '/metadata/external/{identifier}',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["External"],
        summary="Update an external record",
        description="update an external record along with the submission record.",
    )
    async def update_metadata(self, metadata: request_model, identifier):
        client = Minio(
            "play.min.io",
            access_key="Q3AM3UQ867SPQQA43P2F",
            secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
        )
        fp = open('test.txt', 'w')
        fp.write(metadata.json(indent=2))
        fp.close()
        client.fput_object(metadata.identifier, ".hs/aggregations.json", 'test.txt')
        return await self.submit(identifier, metadata.dict())

    @router.get(
        '/metadata/external/{identifier}',
        response_model_exclude_unset=True,
        response_model=response_model,
        tags=["External"],
        summary="Get an external record",
        description="Get an external record along with the submission record.",
    )
    async def get_metadata_repository(self, identifier):
        client = Minio(
            "play.min.io",
            access_key="Q3AM3UQ867SPQQA43P2F",
            secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
        )
        client.fget_object(identifier, ".hs/aggregations.json", 'test.txt')
        with open('test.txt', 'r') as f:
            return json.loads(f.read())

    @router.delete(
        '/metadata/external/{identifier}',
        tags=["External"],
        summary="Delete an external record",
        description="Deletes an external record.",
    )
    async def delete_metadata_repository(self, identifier):
        delete_submission(self.db, self.repository_type, identifier, self.user)
