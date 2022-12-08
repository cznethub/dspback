from datetime import datetime
from typing import Any, List, Optional

from beanie import Document
from pydantic import BaseModel, Field, HttpUrl


class Provider(BaseModel):
    name: str


class TemporalCoverage(BaseModel):
    start: datetime = None
    end: datetime = None


class SpatialCoverage(BaseModel):
    geojson: List[Any]


class Creator(BaseModel):
    name: str


class CreatorList(BaseModel):
    list: List[Creator] = Field(alias="@list", default=[])


class License(BaseModel):
    text: str = None


class Funder(BaseModel):
    name: str = None


class Funding(BaseModel):
    name: Optional[str]
    number: str = None
    funder: List[Funder] = []


class JSONLD(Document):
    repository_identifier: str
    url: HttpUrl
    type: str = Field(alias='@type', default='Dataset')
    provider: Provider
    name: str
    description: str = None
    keywords: List[str]
    temporalCoverage: Optional[TemporalCoverage]
    spatialCoverage: Optional[SpatialCoverage]
    creator: CreatorList  # creator.@list.name
    license: Optional[License]
    funding: List[Funding] = []
    datePublished: Optional[datetime]
    dateCreated: Optional[datetime]
    relations: List[str]
