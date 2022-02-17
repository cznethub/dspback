# generated by datamodel-codegen:
#   filename:  schema.json
#   timestamp: 2022-01-28T18:35:36+00:00
#   https://raw.githubusercontent.com/earthchem/ecl-spec/main/schemas/ECL-JSON-v2.0.0.json

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Extra, Field, constr


class Community(Enum):
    Geochemistry___Petrology = 'Geochemistry & Petrology'
    Cosmochemistry = 'Cosmochemistry'
    Geochronology = 'Geochronology'
    Experimental_Petrology = 'Experimental Petrology'
    Tephra_Data = 'Tephra Data'
    Clumped_Isotopes = 'Clumped Isotopes'
    CZNet = 'CZNet'


class Type(Enum):
    Collection = 'Collection'
    Dataset = 'Dataset'
    Event = 'Event'
    Image = 'Image'
    InteractiveResource = 'InteractiveResource'
    MovingImage = 'MovingImage'
    PhysicalObject = 'PhysicalObject'
    Service = 'Service'
    Software = 'Software'
    Sound = 'Sound'
    StillImage = 'StillImage'
    Text = 'Text'


class Status(Enum):
    incomplete = 'incomplete'
    submitted = 'submitted'
    published = 'published'
    rejected = 'rejected'
    archived = 'archived'


class Identifier(BaseModel):
    class Config:
        extra = Extra.forbid

    scheme: str = Field(..., description='Persistent identifier scheme.')
    schemeURI: str = Field(..., description='URL of the scheme.')
    identifier: str = Field(..., description='Identifier for the resource in the scheme.')
    url: str = Field(..., description='URL of the resource.')


class AdditionalType(Enum):
    Chemistry = 'Chemistry'
    Chemistry_Rock = 'Chemistry:Rock'
    Chemistry_Sediment = 'Chemistry:Sediment'
    Chemistry_Fluid = 'Chemistry:Fluid'
    Chemistry_Gas = 'Chemistry:Gas'
    Geochronology = 'Geochronology'
    Kinetics = 'Kinetics'
    ModelData = 'ModelData'
    Other = 'Other'
    Petrography = 'Petrography'
    Petrology = 'Petrology'
    Petrology_Mineral = 'Petrology:Mineral'
    Petrology_Experimental = 'Petrology:Experimental'
    SampleInfo = 'SampleInfo'
    SocialScience = 'SocialScience'
    Chemistry_ClumpedIsotope = 'Chemistry:ClumpedIsotope'


class Coverage(Enum):
    Space_Planetary = 'Space/Planetary'
    Global = 'Global'
    Regional__Continents__Oceans_ = 'Regional (Continents, Oceans)'
    Other = 'Other'


class Type1(Enum):
    Point = 'Point'
    LineString = 'LineString'
    Polygon = 'Polygon'


class Coordinate(BaseModel):
    lon: float = Field(..., description='longitude')
    lat: float = Field(..., description='latitude')
    alt: Optional[float] = Field(None, description='altitude')


class Geometry(BaseModel):
    class Config:
        extra = Extra.forbid

    type: Type1 = Field(..., description='Type of geometry.')
    coordinates: List[Coordinate]


class Feature(BaseModel):
    class Config:
        extra = Extra.forbid

    geometry: Geometry = Field(..., description='An explanation about the purpose of this instance.')


class SpatialCoverage(BaseModel):
    class Config:
        extra = Extra.forbid

    coverage: Coverage = Field(..., description='An explanation about the purpose of this instance.')
    keywords: List[str]
    features: List[Feature]


class Language(Enum):
    Arabic = 'Arabic'
    Bulgarian = 'Bulgarian'
    Chinese = 'Chinese'
    Croatian = 'Croatian'
    Czech = 'Czech'
    Danish = 'Danish'
    Dutch = 'Dutch'
    English = 'English'
    Finnish = 'Finnish'
    French = 'French'
    German = 'German'
    Greek = 'Greek'
    Hindi = 'Hindi'
    Italian = 'Italian'
    Japanese = 'Japanese'
    Korean = 'Korean'
    Norwegian = 'Norwegian'
    Polish = 'Polish'
    Portuguese = 'Portuguese'
    Russian = 'Russian'
    Spanish = 'Spanish'
    Swedish = 'Swedish'


class Type2(Enum):
    owner = 'owner'


class Identifier1(BaseModel):
    class Config:
        extra = Extra.forbid

    scheme: str = Field(..., description='Persistent identifier scheme for the contributor.')
    schemeURI: str = Field(..., description='URL of the scheme.')
    identifier: str = Field(..., description='Identifier for the creator under specific scheme.')
    url: str = Field(..., description='URL for the creator under specific scheme.')


class Scheme(Enum):
    ROR = 'ROR'


class Identifier2(BaseModel):
    class Config:
        extra = Extra.forbid

    scheme: Scheme = Field(..., description='Persistent identifier scheme for affiliation.')
    schemeURI: str = Field(..., description='URL of the scheme.')
    identifier: str = Field(..., description='Identifier for the affiliation under specific scheme.')
    url: str = Field(..., description='URL for the affiliation under specific scheme.')


class Affiliation(BaseModel):
    class Config:
        extra = Extra.forbid

    name: str
    identifiers: List[Identifier2] = Field(..., description='Identifiers for the affiliation.')


class Creator(BaseModel):
    class Config:
        extra = Extra.forbid

    familyName: str
    additionalName: Optional[str] = Field(None, description='Used for a middle initial.')
    givenName: str
    email: str
    type: Type2 = Field(..., description='The type of creator, controlled vocabulary')
    identifiers: List[Identifier1] = Field(..., description='Identifiers for the creator.')
    affiliation: Affiliation = Field(..., description='Affiliation of the creator.')


class Type3(Enum):
    leadAuthor = 'leadAuthor'
    coAuthor = 'coAuthor'


class Scheme1(Enum):
    ORCID = 'ORCID'


class Identifier3(BaseModel):
    class Config:
        extra = Extra.forbid

    scheme: Scheme1 = Field(..., description='Persistent identifier scheme for the contributor.')
    schemeURI: str = Field(..., description='URL of the scheme.')
    identifier: str = Field(..., description='Identifier for the contributor under specific scheme.')
    url: str = Field(..., description='URL for the contributor under specific scheme.')


class Scheme2(Enum):
    ROR = 'ROR'


class Identifier4(BaseModel):
    class Config:
        extra = Extra.forbid

    scheme: Scheme2 = Field(..., description='Persistent identifier scheme for affiliation.')
    schemeURI: str = Field(..., description='URL of the scheme.')
    identifier: str = Field(..., description='Identifier for the affiliation under specific scheme.')
    url: str = Field(..., description='URL for the affiliation under specific scheme.')


class Affiliation1(BaseModel):
    class Config:
        extra = Extra.forbid

    name: str
    identifiers: List[Identifier4] = Field(..., description='Identifiers for the affiliation.')


class Contributor(BaseModel):
    class Config:
        extra = Extra.forbid

    type: Type3 = Field(..., description='Role of the contributor.')
    familyName: str
    additionalName: Optional[str] = Field(None, description='Used for a middle initial.')
    givenName: str
    email: str
    position: Optional[int] = Field(
        None,
        description="The position of a person in a sequence of contributors, apply only to 'coAuthor'.",
    )
    identifiers: List[Identifier3] = Field(..., description='Identifier for the contributor.')
    affiliation: Optional[Affiliation1] = Field(None, description='Affiliation of the creator.')


class Scheme3(Enum):
    DOI = 'DOI'
    IGSN = 'IGSN'
    SVN = 'SVN'
    R2R = 'R2R'


class Identifier5(BaseModel):
    class Config:
        extra = Extra.forbid

    scheme: Scheme3 = Field(..., description='Persistent identifier scheme for related resources.')
    schemeURI: str = Field(..., description='URL of the scheme.')
    identifier: str = Field(..., description='Identifier for the related resource under specific scheme.')
    url: str = Field(..., description='URL for the related resource under specific scheme.')


class Relation(Enum):
    isCitedBy = 'isCitedBy'
    cites = 'cites'
    isSupplementTo = 'isSupplementTo'
    isSupplementedBy = 'isSupplementedBy'
    isContinuedBy = 'isContinuedBy'
    continues = 'continues'
    isDescribedBy = 'isDescribedBy'
    describes = 'describes'
    hasMetadata = 'hasMetadata'
    isMetadataFor = 'isMetadataFor'
    isNewVersionOf = 'isNewVersionOf'
    isPreviousVersionOf = 'isPreviousVersionOf'
    isPartOf = 'isPartOf'
    hasPart = 'hasPart'
    isReferencedBy = 'isReferencedBy'
    references = 'references'
    isDocumentedBy = 'isDocumentedBy'
    documents = 'documents'
    isCompiledBy = 'isCompiledBy'
    compiles = 'compiles'
    isVariantFormOf = 'isVariantFormOf'
    isOrignialFormOf = 'isOrignialFormOf'
    isIdenticalTo = 'isIdenticalTo'
    isReviewedBy = 'isReviewedBy'
    reviews = 'reviews'
    isDerivedFrom = 'isDerivedFrom'
    isSourceOf = 'isSourceOf'
    requires = 'requires'
    isRequiredBy = 'isRequiredBy'
    isObsoletedBy = 'isObsoletedBy'
    obsoletes = 'obsoletes'
    isPublishedIn = 'isPublishedIn'


class Type4(Enum):
    publication = 'publication'
    phsicalSample = 'phsicalSample'
    volcano = 'volcano'


class RelatedResource(BaseModel):
    class Config:
        extra = Extra.forbid

    bibliographicCitation: str = Field(..., description='A bibliographic reference for the related resource.')
    identifiers: List[Identifier5] = Field(..., description='Identifiers for the related resources.')
    relation: Relation = Field(
        ...,
        description='The relationship of the resource being registered (A) and the related resource (B). Value comes from DataCite RelationType vocabulary.',
    )
    type: Type4 = Field(..., description='Type of the related resource.')


class Identifier6(BaseModel):
    class Config:
        extra = Extra.forbid

    scheme: str = Field(..., description='Persistant identifier scheme.')
    schemeURI: str = Field(..., description='URL of the scheme.')
    identifier: str = Field(..., description='Identifier for the funder under specific scheme.')
    url: str = Field(..., description='URL for the funder under specific scheme.')


class Funder(BaseModel):
    class Config:
        extra = Extra.forbid

    name: str = Field(..., description='Name given to the funder.')
    alternateName: str = Field(..., description='Abbreviation for the given funder name.')
    identifiers: List[Identifier6] = Field(..., description='Identifiers for the funder.')


class Funding(BaseModel):
    class Config:
        extra = Extra.forbid

    identifier: str = Field(..., description='Award number from the grant.')
    funder: Funder = Field(
        ...,
        description='A person or organization that provides money for a particular purpose.',
    )
    url: str = Field(..., description='URL for the grant/award.')


class Format(Enum):
    _asc = '.asc'
    _bin = '.bin'
    _bmp = '.bmp'
    _csv = '.csv'
    _ctf = '.ctf'
    _doc = '.doc'
    _docx = '.docx'
    _f = '.f'
    _geojson = '.geojson'
    _gif = '.gif'
    _h5 = '.h5'
    _hdf = '.hdf'
    _HEIC = '.HEIC'
    _html = '.html'
    _ipynb = '.ipynb'
    _jgw = '.jgw'
    _jpeg = '.jpeg'
    _jpg = '.jpg'
    _js = '.js'
    _json = '.json'
    _kml = '.kml'
    _m = '.m'
    _md = '.md'
    _nc = '.nc'
    _pdf = '.pdf'
    _png = '.png'
    _ppt = '.ppt'
    _pptx = '.pptx'
    _ps = '.ps'
    _rdf = '.rdf'
    _tar_gz = '.tar.gz'
    _tif = '.tif'
    _tiff = '.tiff'
    _tsv = '.tsv'
    _txt = '.txt'
    _xls = '.xls'
    _xlsm = '.xlsm'
    _xlsx = '.xlsx'
    _xml = '.xml'
    _zip = '.zip'


class File(BaseModel):
    class Config:
        extra = Extra.forbid

    name: constr(max_length=512) = Field(..., description='Name given to the file in the resource.')
    fileID: int = Field(..., description='ECL internal identifier for the file in the resource.')
    description: constr(max_length=256) = Field(..., description='Description of the file in the resource.')
    format: Format = Field(..., description='Format of the file in the resource.')
    position: int = Field(..., description='The position of a file in a sequence of all uploading files.')
    size: int = Field(..., description='The size of the file in the resource in bytes.')
    checksum: str = Field(
        ...,
        description='A Checksum is value that allows the contents of a file to be authenticated.',
    )
    uploadDate: constr(regex=r'((?:19|20)[0-9][0-9])-(0?[1-9]|1[012])-(0?[1-9]|[12][0-9]|3[01])') = Field(
        ..., description='Date when the file was uploaded.'
    )


class AlternateName(Enum):
    CC_BY_NC_SA_3_0 = 'CC-BY-NC-SA-3.0'
    CC_BY_NC_SA_4_0 = 'CC-BY-NC-SA-4.0'
    CC_BY_SA_4_0 = 'CC-BY-SA-4.0'
    CC0_1_0 = 'CC0-1.0'


class Identifier7(BaseModel):
    class Config:
        extra = Extra.forbid

    scheme: str = Field(..., description='Persistent identifier scheme.')
    schemeURI: str = Field(..., description='URL of the scheme.')
    identifier: str = Field(..., description='Identifier for the license under the specific scheme.')
    url: str = Field(..., description='URL for the license under the specific scheme.')


class Licence(BaseModel):
    class Config:
        extra = Extra.forbid

    name: str = Field(..., description='Name given to the license.')
    alternateName: AlternateName = Field(..., description='Short identifier given to the license.')
    identifiers: List[Identifier7] = Field(..., description='Identifiers for the license.')


class Ecl20(BaseModel):
    class Config:
        extra = Extra.forbid

    title: constr(max_length=500) = Field(..., description='Title of the resource.')
    description: str = Field(..., description='Description of the resource.')
    community: Community = Field(
        ...,
        description='A network of interacting scientists defined by ECL. Value comes from ECL controlled vocabulary.',
    )
    type: Type = Field(
        ...,
        description='The nature or genre of the resource.Values come from DCMI Type Vocabulary.',
    )
    status: Status = Field(
        ...,
        description='Indication of the progress status of the resource. Value comes from ECL controlled vocabulary.',
    )
    identifiers: List[Identifier] = Field(..., description='Identifiers for the resource.', max_items=1)
    dateCreated: constr(regex=r'((?:19|20)[0-9][0-9])-(0?[1-9]|1[012])-(0?[1-9]|[12][0-9]|3[01])') = Field(
        ..., description='The date on which the resource was created.'
    )
    dateIssued: Optional[constr(regex=r'((?:19|20)[0-9][0-9])-(0?[1-9]|1[012])-(0?[1-9]|[12][0-9]|3[01])')] = Field(
        None, description='The date on which The DOI was assigned to the resource.'
    )
    datePublished: constr(regex=r'((?:19|20)[0-9][0-9])-(0?[1-9]|1[012])-(0?[1-9]|[12][0-9]|3[01])') = Field(
        ...,
        description='The date of the files contained in the resource to be allowed for downloading.',
    )
    dateModified: constr(regex=r'((?:19|20)[0-9][0-9])-(0?[1-9]|1[012])-(0?[1-9]|[12][0-9]|3[01])') = Field(
        ..., description='The date on which the resource was most recently modified.'
    )
    additionalTypes: List[AdditionalType] = Field(
        ...,
        description='The science domain of the content(analysis data, image, etc.) included in the resource. Values come from ECL controlled vocabulary.',
    )
    keywords: List[str] = Field(..., description='Free form keywords for the resource.')
    spatialCoverage: SpatialCoverage = Field(..., description='An explanation about the purpose of this instance.')
    language: Language = Field(..., description='The language used for the content of the resource.')
    creators: List[Creator] = Field(..., description='The people who create and maintain resource metadata.')
    contributors: List[Contributor] = Field(..., description='Contributors for the resource.')
    relatedResources: List[RelatedResource] = Field(
        ...,
        description='A related resource(publication,physical sample, volcano that is referenced, cited, or otherwise pointed to by the described resource..',
    )
    fundings: List[Funding] = Field(..., description='Source of grants/awards which have funded the resource.')
    files: List[File] = Field(..., description='Files attached to the resource.')
    licence: Licence = Field(..., description='The license for all files contained in the resource.')
