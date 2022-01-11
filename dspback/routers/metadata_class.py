import json
import requests

from database.models import RepositoryTokenTable
from fastapi import Depends, HTTPException
from fastapi_restful.cbv import cbv
from fastapi_restful.inferring_router import InferringRouter
from hsmodels.schemas.resource import ResourceMetadataIn, ResourceMetadata
from requests import Session
from starlette.responses import JSONResponse

from dspback.config import repository_config
from dspback.database.models import UserTable
from dspback.database.procedures import delete_submission
from dspback.dependencies import get_db, get_current_user, get_repository
from dspback.routers.submissions import submit_record
from dspback.schemas import RepositoryType

router = InferringRouter()


class MetadataRoutes:
    db: Session = Depends(get_db)
    user: UserTable = Depends(get_current_user)
    repository: RepositoryTokenTable = Depends(get_repository)

    request_model = None
    response_model = None
    repository_name = None

    def __init__(self):
        if self.request_model is None:
            raise ValueError("field request_model must be defined on the child class")
        if self.response_model is None:
            raise ValueError("field response_model must be defined on the child class")
        if self.repository_name is None:
            raise ValueError("field repository_name must be defined on the child class")

        if self.repository_name not in repository_config:
            raise ValueError(f"No configuration found for {self.repository_name}")

        if "read" not in repository_config[self.repository_name]:
            raise ValueError(f"No 'read' value found for {self.repository_name} configuration")
        self.read_url = repository_config[self.repository_name]["read"]

        if "create" not in repository_config[self.repository_name]:
            raise ValueError(f"No 'create' value found for {self.repository_name} configuration")
        self.create_url = repository_config[self.repository_name]["create"]

        if "update" not in repository_config[self.repository_name]:
            raise ValueError(f"No 'update' value found for {self.repository_name} configuration")
        self.update_url = repository_config[self.repository_name]["update"]

        if "delete" not in repository_config[self.repository_name]:
            raise ValueError(f"No 'delete' value found for {self.repository_name} configuration")
        self.delete_url = repository_config[self.repository_name]["delete"]


@cbv(router)
class HydroShareMetadataRoutes(MetadataRoutes):

    request_model = ResourceMetadataIn
    response_model = ResourceMetadata
    repository_name = "hydroshare"

    async def submit_with_retrieve(self, identifier):
        json_metadata = await self.get_metadata_repository(identifier)
        self.submit(identifier, json_metadata)

    def submit(self, identifier, json_metadata):
        submit_record(self.db, self.repository.type, identifier, self.user, json_metadata)

    @router.post('/metadata/{repository}')
    async def create_metadata_repository(self, metadata: request_model) -> response_model:
        response = requests.post(self.create_url, data=metadata.json(),
                                 params={"access_token": self.repository.access_token},
                                 headers={"Content-Type": "application/json"},
                                 timeout=15.0)

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        identifier = response.json()["resource_id"]
        json_metadata = await self.get_metadata_repository(identifier)

        self.submit(identifier=identifier, json_metadata=json_metadata)
        return JSONResponse(json_metadata, status_code=201)

    @router.put('/metadata/{repository}/{identifier}')
    async def update_metadata(self, metadata: request_model, identifier) -> None:
        response = requests.put(self.update_url % identifier, data=metadata.json(skip_defaults=True),
                                headers={"Content-Type": "application/json"},
                                params={"access_token": self.repository.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        await self.submit_with_retrieve(identifier)

    @router.get('/metadata/{repository}/{identifier}')
    async def get_metadata_repository(self, identifier) -> response_model:
        response = requests.get(self.read_url % identifier,
                                params={"access_token": self.repository.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = json.loads(response.text)

        self.submit(identifier=identifier, json_metadata=json_metadata)
        return json_metadata

    @router.delete('/metadata/{repository}/{identifier}')
    async def delete_metadata_repository(self, repository: RepositoryType, identifier):
        response = requests.delete(self.delete_url % identifier,
                                   params={"access_token": self.repository.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        delete_submission(self.db, repository, identifier, self.user)
