from fastapi import Depends
from fastapi_restful.inferring_router import InferringRouter
from requests import Session

from dspback.config import Settings, get_settings, repository_config
from dspback.dependencies import get_current_repository_token, get_current_user
from dspback.pydantic_schemas import User
from dspback.routers.submissions import submit_record

router = InferringRouter()


class MetadataRoutes:
    user: User = Depends(get_current_user)
    settings: Settings = Depends(get_settings)

    request_model = None
    response_model = None
    repository_type = None

    async def submit(self, request, identifier, json_metadata=None):
        if json_metadata is None:
            json_metadata = await self._retrieve_metadata_from_repository(request, identifier)
        await submit_record(self.repository_type, identifier, self.user, json_metadata)
        return json_metadata

    async def access_token(self, request):
        repository_token = await get_current_repository_token(request, self.repository_type, self.user, self.settings)
        return repository_token.access_token

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
