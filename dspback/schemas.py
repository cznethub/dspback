from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, root_validator, validator


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
    type: RepositoryType = None
    access_token: str = None
    repo_user_id: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: str = None
    expires_at: str = None


class RepositoryToken(RepositoryTokenBase):
    class Config:
        orm_mode = True

    id: int = None


class SubmissionBase(BaseModel):
    title: str = None
    authors: List[str] = []
    repo_type: RepositoryType = None
    identifier: str = None
    submitted: datetime = None

    @validator('authors', pre=True)
    def extract_author_names(cls, values):
        authors = []
        for author in values:
            if hasattr(author, 'name'):
                authors.append(author.name)
            else:
                authors.append(author)
        return authors


class Submission(SubmissionBase):
    class Config:
        orm_mode = True

    id: int = None


class UserBase(BaseModel):
    name: str = None
    # email: EmailStr = None
    orcid: str = None
    access_token: str = None
    refresh_token: str = None
    expires_in: int = None
    expires_at: int = None
    repository_tokens: List[RepositoryToken] = []
    submissions: List[Submission] = []


class User(UserBase):
    class Config:
        orm_mode = True

    id: Optional[int] = None

    def repository_token(self, repo_type: RepositoryType) -> RepositoryToken:
        return next(filter(lambda repo: repo.type == repo_type, self.repository_tokens), None)


class BaseRecord(BaseModel):
    def to_submission(self) -> Submission:
        raise NotImplementedError()


class ZenodoRecord(BaseRecord):
    class Creator(BaseModel):
        name: str = None

    title: str = None
    creators: List[Creator] = []
    modified: datetime = None
    record_id: str = None

    @root_validator(pre=True)
    def extract_metadata(cls, values):
        values.update(values['metadata'])
        del values['metadata']
        return values

    def to_submission(self) -> Submission:
        return Submission(
            title=self.title,
            authors=[creator.name for creator in self.creators],
            repo_type=RepositoryType.ZENODO,
            submitted=self.modified,
            identifier=self.record_id,
        )


class HydroShareRecord(BaseRecord):
    class Creator(BaseModel):
        name: str = None

    title: str = None
    creators: List[Creator] = []
    modified: datetime = None
    identifier: str = None

    @validator("identifier")
    def extract_identifier(cls, value):
        return value.split("/")[-1]

    def to_submission(self) -> Submission:
        return Submission(
            title=self.title,
            authors=[creator.name for creator in self.creators],
            repo_type=RepositoryType.HYDROSHARE,
            submitted=self.modified,
            identifier=self.identifier,
        )
