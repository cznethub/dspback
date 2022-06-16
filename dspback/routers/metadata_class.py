from fastapi import Depends, HTTPException
from fastapi_restful.inferring_router import InferringRouter
from requests import Session

from dspback.config import repository_config
from dspback.database.models import RepositoryTokenTable, UserTable
from dspback.dependencies import get_current_user, get_db
from dspback.routers.submissions import submit_record

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
