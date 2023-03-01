from datetime import datetime
from typing import Any, List, Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field, HttpUrl

from dspback.config import get_settings


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
    context: HttpUrl = Field(alias='@context', default='https://schema.org')
    repository_identifier: str
    url: Indexed(HttpUrl, unique=True)
    type: str = Field(alias='@type', default='Dataset')
    provider: Provider
    name: Optional[str]
    description: Optional[str]
    keywords: Optional[List[str]]
    creator: Optional[CreatorList]  # creator.@list.name
    funding: Optional[List[Funding]]

    temporalCoverage: Optional[TemporalCoverage]
    spatialCoverage: Optional[SpatialCoverage]
    license: Optional[License]
    datePublished: Optional[datetime]
    dateCreated: Optional[datetime]
    relations: Optional[List[str]] = []

    class Settings:
        name = "discovery"
