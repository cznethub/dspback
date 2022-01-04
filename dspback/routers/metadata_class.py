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

router = InferringRouter()


@cbv(router)
class MetadataRoutes:
    db: Session = Depends(get_db)
    user: UserTable = Depends(get_current_user)
    repository: RepositoryTokenTable = Depends(get_repository)

    request_model = ResourceMetadataIn
    response_model = ResourceMetadata

    repository_name = "hydroshare"
    read_url = repository_config[repository_name]["read"]
    create_url = repository_config[repository_name]["create"]
    update_url = repository_config[repository_name]["update"]
    delete_url = repository_config[repository_name]["delete"]

    async def submit(self, identifier, json_metadata=None):
        if json_metadata is None:
            json_metadata = await self.get_metadata_repository(identifier)
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

        await self.submit(identifier=identifier, json_metadata=json_metadata)
        return JSONResponse(json_metadata, status_code=201)

    @router.put('/metadata/{repository}/{identifier}')
    async def update_metadata(self, metadata: request_model, repository, identifier) -> None:
        response = requests.put(self.update_url % identifier, data=metadata.json(),
                                headers={"Content-Type": "application/json"},
                                params={"access_token": self.repository.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        await self.submit(identifier)

    @router.get('/metadata/{repository}/{identifier}')
    async def get_metadata_repository(self, identifier) -> response_model:
        response = requests.get(self.read_url % identifier,
                                params={"access_token": self.repository.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return json.loads(response.text)

    @router.delete('/metadata/{repository}/{identifier}')
    async def delete_metadata_repository(self, repository, identifier) -> response_model:
        response = requests.delete(self.delete_url % identifier,
                                   params={"access_token": self.repository.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        delete_submission(self.db, repository, identifier, self.user)

        return json.loads(response.text)
