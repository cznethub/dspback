from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class ORCIDResponse(BaseModel):
    name: str
    orcid: str
    access_token: str
    expires_in: str
    expires_at: str
    refresh_token: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    orcid: Optional[str] = None


class StringEnum(str, Enum):
    pass


class RepositoryType(StringEnum):
    ZENODO = "zenodo"
    HYDROSHARE = "hydroshare"


class ORCIDResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    expires_in: int
    scope: str
    name: str
    orcid: str
    id_token: str
    expires_at: str


class RepositoryTokenBase(BaseModel):
    id: int = None
    type: RepositoryType = None
    access_token: str = None
    repo_user_id: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: str = None
    expires_at: str = None


class RepositoryToken(RepositoryTokenBase):
    class Config:
        orm_mode = True


class UserBase(BaseModel):
    id: Optional[int] = None
    name: str = None
    # email: EmailStr = None
    orcid: str = None
    access_token: str = None
    refresh_token: str = None
    expires_in: int = None
    expires_at: int = None
    repository_tokens: List[RepositoryToken] = []


class User(UserBase):
    class Config:
        orm_mode = True

    def repository_token(self, repo_type: RepositoryType) -> RepositoryToken:
        return next(filter(lambda repo: repo.type == repo_type, self.repository_tokens), None)
