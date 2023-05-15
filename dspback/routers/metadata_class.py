from fastapi import Depends
from fastapi_restful.inferring_router import InferringRouter

from dspback.config import Settings, get_settings
from dspback.authentication.user import get_current_user
from dspback.pydantic_schemas import User
from dspback.routers.submissions import submit_record

router = InferringRouter()


def exists_and_is(property: str, dictionary: dict):
    return property in dictionary and dictionary[property] is not None


class MetadataRoutes:
    user: User = Depends(get_current_user)
    settings: Settings = Depends(get_settings)

    request_model = None
    response_model = None

    async def submit(self, request, identifier, json_metadata=None):
        if json_metadata is None:
            json_metadata = await self._retrieve_metadata_from_repository(request, identifier)
        await submit_record(identifier, self.user, json_metadata["metadata"])
        return json_metadata

    def wrap_metadata(self, metadata: dict, published: bool):
        return {"metadata": metadata, "published": published}

    def __init__(self):
        if self.request_model is None:
            raise ValueError("field request_model must be defined on the child class")
        if self.response_model is None:
            raise ValueError("field response_model must be defined on the child class")
        if self.repository_type is None:
            raise ValueError("field repository_name must be defined on the child class")
