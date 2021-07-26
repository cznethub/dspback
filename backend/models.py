from enum import Enum
from typing import List, Optional

from pydantic import UUID4, BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    orcid: Optional[str] = None

class StringEnum(str, Enum):
    pass

class Repo(StringEnum):
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

class RepositoryBase(BaseModel):
    id: UUID4 = None
    repo: Repo = None
    access_token: str = None
    repo_user_id: Optional[str] = None
    refresh_token: Optional[str] = None

class Repository(RepositoryBase):

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    id: Optional[UUID4] = None
    name: str = None
    #email: EmailStr = None
    orcid: str = None
    access_token: str = None
    refresh_token: str = None
    expires_in: int = None
    expires_at: int = None
    repositories: List[Repository] = None

class User(UserBase):

    class Config:
        orm_mode = True