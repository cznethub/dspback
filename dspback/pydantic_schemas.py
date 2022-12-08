from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from geojson import Feature, Point
from pydantic import BaseModel, Field, HttpUrl, root_validator, validator

from dspback.config import get_settings
from dspback.utils.jsonld.pydantic_schemas import JSONLD


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

    @validator('authors', pre=True, allow_reuse=True)
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

    def to_submission(self, identifier) -> Submission:
        raise NotImplementedError()


class ZenodoRecord(BaseRecord):
    class Creator(BaseModel):
        name: str = None

    class RelatedIdentifier(BaseModel):
        identifier: str = None
        relation: str = None

    title: str = None
    description: str = None
    keywords: List[str] = []
    creators: List[Creator] = []
    license: str = None
    notes: str = None
    publication_date: datetime = None
    relations: List[RelatedIdentifier] = []
    modified: datetime = None
    created: datetime = None
    record_id: str = None

    @root_validator(pre=True, allow_reuse=True)
    def extract_metadata(cls, values):
        values.update(values['metadata'])
        del values['metadata']
        return values

    @validator('publication_date', pre=True)
    def parse_publication_date(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, '%Y-%m-%d')
        return value

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

    def to_jsonld(self, identifier):
        settings = get_settings()
        view_url = settings.zenodo_view_url % identifier
        return JSONLD(
            url=view_url,
            provider={'name': 'Zenodo'},
            name=self.title,
            description=self.description,
            keywords=self.keywords,
            creator={'@list': [{'name': creator.name} for creator in self.creators]},
            license={'text': self.license},
            funding=[{'name': self.notes, 'funder': [{'name': self.notes}]}],  # need to do some regex magic
            datePublished=self.publication_date,
            dateCreated=self.created,
            relations=[f'{relation.name} - {relation.identifier}' for relation in self.relations],
        )


class HydroShareRecord(BaseRecord):
    class PeriodCoverage(BaseModel):
        start: datetime = None
        end: datetime = None

    class SpatialCoverage(BaseModel):
        type: str = None
        northlimit: float = None
        eastlimit: float = None
        southlimit: float = None
        westlimit: float = None
        north: float = None
        east: float = None

        @property
        def geojson(self):
            if self.type == 'box':
                return [float(self.northlimit), float(self.southlimit), float(self.eastlimit), float(self.westlimit)]
            else:
                return [Feature(geometry=Point([float(self.east), float(self.north)]))]

    class Creator(BaseModel):
        name: str = None

    class Award(BaseModel):
        funding_agency_name: str = None
        title: str = None
        number: str = None

    class Relation(BaseModel):
        value: str = None

    class Rights(BaseModel):
        statement: str = None

    title: str = None
    description: str = None
    subjects: List[str] = []
    period_coverage: PeriodCoverage = PeriodCoverage()
    spatial_coverage: SpatialCoverage = SpatialCoverage()
    creators: List[Creator] = []
    awards: List[Award]
    rights: Rights
    relations: List[Relation] = []
    published: Optional[datetime]
    modified: Optional[datetime]
    created: Optional[datetime]
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

    def to_jsonld(self, identifier):
        settings = get_settings()
        view_url = settings.hydroshare_view_url % identifier
        return JSONLD(
            url=view_url,
            provider={'name': 'HydroShare'},
            name=self.title,
            description=self.description,
            keywords=self.subjects,
            temporalCoverage=self.period_coverage.dict(),
            spatialCoverage={"geojson": self.spatial_coverage.geojson},
            creator={'@list': [{'name': creator.name} for creator in self.creators]},
            license={'text': self.rights.statement},
            funding=[
                {"name": award.title, "number": award.number, "funder": [{"name": award.funding_agency_name}]}
                for award in self.awards
            ],
            datePublished=self.published,
            dateCreated=self.created,
            relations=[relation.value for relation in self.relations],
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
