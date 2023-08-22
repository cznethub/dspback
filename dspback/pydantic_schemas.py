from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Union

from beanie import Document, Link
from geojson import Feature, Point, Polygon
from pydantic import BaseModel, EmailStr, Field, HttpUrl, root_validator, validator

from dspback.config import get_settings
from dspback.schemas.discovery import JSONLD


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


class RepositoryToken(Document):
    type: RepositoryType = None
    access_token: str = None
    refresh_token: Optional[str] = None
    expires_in: int = None
    expires_at: int = None


class Submission(Document):
    title: str = None
    authors: List[str] = []
    repo_type: RepositoryType = None
    identifier: str = None
    submitted: datetime = datetime.utcnow()
    url: HttpUrl = None
    metadata_json: str = "{}"

    @validator('authors', pre=True, allow_reuse=True)
    def extract_author_names(cls, values):
        authors = []
        for author in values:
            if hasattr(author, 'name'):
                authors.append(author.name)
            else:
                authors.append(author)
        return authors


class User(Document):
    name: str
    email: Optional[EmailStr]
    orcid: str
    access_token: Optional[str]
    orcid_access_token: Optional[str]
    refresh_token: Optional[str]
    expires_in: Optional[int]
    expires_at: Optional[int]
    repository_tokens: List[Link[RepositoryToken]] = []
    submissions: List[Link[Submission]] = []

    def submission(self, identifier: str) -> Submission:
        return next(filter(lambda submission: submission.identifier == identifier, self.submissions), None)

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
    license: Optional[str]
    notes: str = ""
    publication_date: Optional[datetime]
    relations: Optional[List[RelatedIdentifier]] = []
    modified: Optional[datetime]
    created: Optional[datetime]
    record_id: str

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
                return [
                    Feature(
                        geometry=Polygon(
                            [
                                float(self.northlimit),
                                float(self.southlimit),
                                float(self.eastlimit),
                                float(self.westlimit),
                            ]
                        )
                    )
                ]
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
    period_coverage: Optional[PeriodCoverage]
    spatial_coverage: Optional[SpatialCoverage]
    creators: List[Creator] = []
    awards: List[Award] = []
    rights: Optional[Rights]
    relations: Optional[List[Relation]] = []
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


class EarthChemRecord(BaseRecord):
    class Contributor(BaseModel):
        givenName: str = None
        familyName: str = None

        @property
        def name(self):
            return f"{self.familyName}, {self.givenName}"

    class Funding(BaseModel):
        class Funder(BaseModel):
            name: str

        identifier: str
        funder: Funder

    class RelatedResource(BaseModel):
        bibliographicCitation: str

    class License(BaseModel):
        alternateName: str

    title: str = None
    description: str = None
    keywords: List[str] = []
    contributors: List[Contributor] = []
    leadAuthor: Contributor
    license: Optional[License]
    fundings: List[Funding] = []
    datePublished: Optional[date]
    relatedResources: Optional[List[RelatedResource]] = []

    def to_submission(self, identifier) -> Submission:
        settings = get_settings()
        view_url = settings.earthchem_public_view_url % identifier
        authors = [contributor.name for contributor in self.contributors]
        authors.insert(0, self.leadAuthor.name)
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

    class Provider(BaseModel):
        name: str

    class TemporalCoverage(BaseModel):
        start: datetime
        end: datetime

    class SpatialCoverage(BaseModel):
        type: Optional[str]
        name: Optional[str]
        north: Optional[float]
        east: Optional[float]
        northlimit: Optional[float]
        southlimit: Optional[float]
        eastlimit: Optional[float]
        westlimit: Optional[float]

        @property
        def geojson(self):
            if self.type == 'box':
                return [
                    Feature(
                        geometry=Polygon(
                            [
                                float(self.northlimit),
                                float(self.southlimit),
                                float(self.eastlimit),
                                float(self.westlimit),
                            ]
                        )
                    )
                ]
            else:
                return [Feature(geometry=Point([float(self.east), float(self.north)]))]

    class License(BaseModel):
        description: str

    class Funder(BaseModel):
        fundingAgency: str
        awardNumber: str
        awardName: str

    class Relation(BaseModel):
        value: str

    name: str
    provider: Provider
    description: str
    keywords: List[str] = []
    temporalCoverage: Optional[TemporalCoverage]
    spatialCoverage: Optional[SpatialCoverage]
    creators: List[Creator] = []
    license: Optional[License]
    funders: List[Funder] = []
    datePublished: Optional[Union[int, datetime]]
    relations: Optional[List[Relation]] = []
    dateCreated: Optional[Union[int, datetime]]
    repository_identifier: str = None
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

    def to_jsonld(self, identifier) -> JSONLD:
        required = {
            "repository_identifier": identifier,
            "url": self.url,
            "provider": {'name': self.provider.name},
            "name": self.name,
            "description": self.description,
            "keywords": self.keywords,
            "creator": {'@list': self.creators},
            "funding": [
                {"name": funder.awardName, "identifier": funder.awardNumber, "funder": {"name": funder.fundingAgency}}
                for funder in self.funders
            ],
        }
        optional = {}
        if self.temporalCoverage:
            optional["temporalCoverage"] = self.temporalCoverage
        if self.spatialCoverage:
            optional["spatialCoverage"] = {"geojson": self.spatialCoverage.geojson}
        if self.license:
            optional["license"] = {'text': self.license.description}
        if self.datePublished:
            if isinstance(self.datePublished, int):
                optional["datePublished"] = datetime(self.datePublished, 1, 1)
            else:
                optional["datePublished"] = self.datePublished
        if self.dateCreated:
            if isinstance(self.dateCreated, int):
                optional["dateCreated"] = datetime(self.dateCreated, 1, 1)
            else:
                optional["dateCreated"] = self.dateCreated
        if self.relations:
            optional["relations"] = [relation.value for relation in self.relations]
        return JSONLD(**required, **optional)
