import json
import requests

from database.models import RepositoryTokenTable
from fastapi import Depends, HTTPException
from fastapi_restful.cbv import cbv
from fastapi_restful.inferring_router import InferringRouter
from hsmodels.schemas.resource import ResourceMetadataIn, ResourceMetadata
from requests import Session
from dspback.pydantic_schemas import RepositoryType
from starlette.responses import JSONResponse

from dspback.config import repository_config
from dspback.database.models import UserTable
from dspback.database.procedures import delete_submission
from dspback.dependencies import get_db, get_current_user
from dspback.routers.submissions import submit_record
from dspback.schemas.zenodo.model import ZenodoDatasetsSchemaForCzNetV100, NotRequiredZenodo, ResponseModelZenodo
from dspback.schemas.eartchem.model import Ecl20

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
        return repository_token.access_token

    async def submit(self, identifier, json_metadata=None):
        if json_metadata is None:
            json_metadata = await self.get_metadata_repository(identifier, unpack=False)
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


@cbv(router)
class HydroShareMetadataRoutes(MetadataRoutes):

    request_model = ResourceMetadataIn
    response_model = ResourceMetadata
    repository_type = RepositoryType.HYDROSHARE

    @router.post('/metadata/hydroshare')
    async def create_metadata_repository(self, metadata: request_model) -> response_model:
        response = requests.post(self.create_url, data=metadata.json(),
                                 params={"access_token": self.access_token},
                                 headers={"Content-Type": "application/json"},
                                 timeout=15.0)

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        identifier = response.json()["resource_id"]
        json_metadata = await self.get_metadata_repository(identifier)

        return JSONResponse(json_metadata, status_code=201)

    @router.put('/metadata/hydroshare/{identifier}')
    async def update_metadata(self, metadata: request_model, identifier) -> response_model:
        response = requests.put(self.update_url % identifier, data=metadata.json(skip_defaults=True),
                                headers={"Content-Type": "application/json"},
                                params={"access_token": self.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = await self.submit(identifier)
        return json_metadata

    @router.get('/metadata/hydroshare/{identifier}')
    async def get_metadata_repository(self, identifier, **kwargs) -> response_model:
        response = requests.get(self.read_url % identifier,
                                params={"access_token": self.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = json.loads(response.text)

        await self.submit(identifier=identifier, json_metadata=json_metadata)
        return json_metadata

    @router.delete('/metadata/hydroshare/{identifier}')
    async def delete_metadata_repository(self, identifier):
        response = requests.delete(self.delete_url % identifier,
                                   params={"access_token": self.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        delete_submission(self.db, self.repository_type, identifier, self.user)

    @router.put('/submit/hydroshare/{identifier}', name="submit")
    async def submit_repository_record(self, identifier: str):
        await self.submit(identifier)


@cbv(router)
class ZenodoMetadataRoutes(MetadataRoutes):

    request_model = ZenodoDatasetsSchemaForCzNetV100
    request_model_update = NotRequiredZenodo
    response_model = ResponseModelZenodo
    repository_type = RepositoryType.ZENODO

    @router.post('/metadata/zenodo')
    async def create_metadata_repository(self, metadata: request_model) -> response_model:
        metadata_json = {"metadata": json.loads(metadata.json(exclude_none=True))}
        response = requests.post(self.create_url, json=metadata_json,
                                 params={"access_token": self.access_token},
                                 headers={"Content-Type": "application/json"},
                                 timeout=15.0)

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        identifier = response.json()["record_id"]
        json_metadata = await self.get_metadata_repository(identifier)

        return JSONResponse(json_metadata, status_code=201)

    @router.put('/metadata/zenodo/{identifier}')
    async def update_metadata(self, metadata: request_model_update, identifier) -> response_model:
        existing_metadata = await self.get_metadata_repository(identifier)
        incoming_metadata = metadata.json(skip_defaults=True, exclude_unset=True)
        merged_metadata = {"metadata": {**existing_metadata, **json.loads(incoming_metadata)}}
        response = requests.put(self.update_url % identifier, json=merged_metadata,
                                headers={"Content-Type": "application/json"},
                                params={"access_token": self.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        await self.submit(identifier)
        return await self.get_metadata_repository(identifier)

    @router.get('/metadata/zenodo/{identifier}')
    async def get_metadata_repository(self, identifier, unpack=True) -> response_model:
        response = requests.get(self.read_url % identifier, params={"access_token": self.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = json.loads(response.text)

        await self.submit(identifier=identifier, json_metadata=json_metadata)

        return json_metadata["metadata"] if unpack else json_metadata

    @router.delete('/metadata/zenodo/{identifier}')
    async def delete_metadata_repository(self, identifier):
        response = requests.delete(self.delete_url % identifier,
                                   params={"access_token": self.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        delete_submission(self.db, self.repository_type, identifier, self.user)

    @router.put('/submit/zenodo/{identifier}', name="submit")
    async def submit_repository_record(self, identifier: str):
        await self.submit(identifier)


@cbv(router)
class EarthChemMetadataRoutes(MetadataRoutes):

    request_model = Ecl20
    request_model_update = Ecl20
    response_model = Ecl20
    repository_type = RepositoryType.EARTHCHEM

    @router.post('/metadata/zenodo')
    async def create_metadata_repository(self, metadata: request_model) -> response_model:
        raise NotImplementedError("EarthChem metadata endpoints are not implemented yet")

    @router.put('/metadata/zenodo/{identifier}')
    async def update_metadata(self, metadata: request_model_update, identifier) -> response_model:
        raise NotImplementedError("EarthChem metadata endpoints are not implemented yet")

    @router.get('/metadata/zenodo/{identifier}')
    async def get_metadata_repository(self, identifier, unpack=True) -> response_model:
        raise NotImplementedError("EarthChem metadata endpoints are not implemented yet")

    @router.delete('/metadata/zenodo/{identifier}')
    async def delete_metadata_repository(self, identifier):
        raise NotImplementedError("EarthChem metadata endpoints are not implemented yet")

    @router.put('/submit/zenodo/{identifier}', name="submit")
    async def submit_repository_record(self, identifier: str):
        raise NotImplementedError("EarthChem metadata endpoints are not implemented yet")
