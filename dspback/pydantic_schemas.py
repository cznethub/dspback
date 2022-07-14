import base64
import json
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, root_validator, validator

from dspback.config import get_settings


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
    orcid: Optional[str] = Field(alias="sub")
    expiration: Optional[int] = Field(alias="exp")


class StringEnum(str, Enum):
    pass


class RepositoryType(StringEnum):
    ZENODO = "zenodo"
    HYDROSHARE = "hydroshare"
    EARTHCHEM = "earthchem"
    EXTERNAL = "external"


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
    submitted: datetime = datetime.utcnow()
    url: HttpUrl = None

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
    orcid_access_token: str = None
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
        settings = get_settings()
        view_url = settings.zenodo_view_url % identifier
        return Submission(
            title=self.title,
            authors=[creator.name for creator in self.creators],
            repo_type=RepositoryType.ZENODO,
            submitted=datetime.utcnow(),
            identifier=identifier,
            url=view_url,
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
        settings = get_settings()
        view_url = settings.hydroshare_view_url
        view_url = view_url % identifier
        return Submission(
            title=self.title,
            authors=[creator.name for creator in self.creators],
            repo_type=RepositoryType.HYDROSHARE,
            submitted=datetime.utcnow(),
            identifier=identifier,
            url=view_url,
        )


class EarthChemRecord(BaseRecord):
    class Contributor(BaseModel):
        givenName: str = None
        familyName: str = None

    title: str = None
    contributors: List[Contributor] = []
    leadAuthor: Contributor = None

    def to_submission(self, identifier) -> Submission:
        settings = get_settings()
        view_url = settings.earthchem_view_url
        view_url = view_url % identifier
        authors = [f"{contributor.familyName}, {contributor.givenName}" for contributor in self.contributors]
        authors.insert(0, f"{self.leadAuthor.familyName}, {self.leadAuthor.givenName}")
        return Submission(
            title=self.title,
            authors=authors,
            repo_type=RepositoryType.EARTHCHEM,
            submitted=datetime.utcnow(),
            identifier=identifier,
            url=view_url,
        )


class ExternalRecord(BaseRecord):
    class Creator(BaseModel):
        name: str = None

    name: str = None
    creators: List[Creator] = []
    identifier: str = None
    url: HttpUrl = None

    def to_submission(self, identifier) -> Submission:
        return Submission(
            title=self.name,
            authors=[creator.name for creator in self.creators],
            repo_type=RepositoryType.EXTERNAL,
            submitted=datetime.utcnow(),
            identifier=identifier,
            url=self.url,
        )
