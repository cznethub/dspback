import base64
import json
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
    GITLAB = "gitlab"


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
    def to_submission(self, identifier) -> Submission:
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

    def to_submission(self, identifier) -> Submission:
        return Submission(
            title=self.title,
            authors=[creator.name for creator in self.creators],
            repo_type=RepositoryType.ZENODO,
            submitted=self.modified,
            identifier=identifier,
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

    def to_submission(self, identifier) -> Submission:
        return Submission(
            title=self.title,
            authors=[creator.name for creator in self.creators],
            repo_type=RepositoryType.HYDROSHARE,
            submitted=self.modified,
            identifier=identifier,
        )


class GitLabRecord(BaseRecord):

    content: str = None
    file_path: str = None
    creators: List[str] = []
    submitted: datetime = datetime.now()

    @validator("content")
    def base64_decode(cls, value):
        try:
            decodedBytes = base64.b64decode(value)
        except Exception:
            return value
        decodedStr = str(decodedBytes, "utf-8")
        return decodedStr

    def to_submission(self, identifier) -> Submission:
        content = json.loads(self.content)
        # TODO content should have creators and moified?  or maybe pull that from the commit?
        return Submission(
            title=content['title'],
            authors=[creator.name for creator in self.creators],
            repo_type=RepositoryType.GITLAB,
            submitted=self.submitted,
            identifier=identifier,
        )
