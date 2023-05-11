from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

from beanie import Document, Link
from geojson import Feature, Point, Polygon
from pydantic import BaseModel, EmailStr, Field, HttpUrl, validator

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


class Submission(Document):
    title: str = None
    authors: List[str] = []
    identifier: str = None
    submitted: datetime = datetime.utcnow()
    url: HttpUrl = None
    metadata_json: str = {}

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
    preferred_username: str
    submissions: List[Link[Submission]] = []

    def submission(self, identifier: str) -> Submission:
        return next(filter(lambda submission: submission.identifier == identifier, self.submissions), None)


class BaseRecord(BaseModel):
    def to_submission(self, identifier) -> Submission:
        raise NotImplementedError()


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
