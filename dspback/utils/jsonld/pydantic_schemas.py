from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, HttpUrl


class Provider(BaseModel):
    name: str


class TemporalCoverage(BaseModel):
    start: datetime = None
    end: datetime = None


class SpatialCoverage(BaseModel):
    pass


class Creator(BaseModel):
    name: str


class CreatorList(BaseModel):
    list: List[Creator] = Field(alias="@list", default=[])


class License(BaseModel):
    text: str = None
    url: HttpUrl = None


class Funder(BaseModel):
    name: str = None


class Funding(BaseModel):
    name: str = None
    funder: List[Funder] = []


class JSONLD(BaseModel):
    url: HttpUrl
    type: str = Field(alias='@type', default='Dataset')
    provider: Provider
    name: str
    description: str
    keywords: List[str]
    temporalCoverage: TemporalCoverage = TemporalCoverage()
    spatialCoverage: SpatialCoverage = SpatialCoverage()
    creator: CreatorList  # creator.@list.name
    license: License = License()
    funding: Funding = Funding()
    datePublished: datetime
    dateCreated: datetime
    relations: List[str]
