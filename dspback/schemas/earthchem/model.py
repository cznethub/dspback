# generated by datamodel-codegen:
#   filename:  schema.json
#   timestamp: 2022-06-22T18:30:02+00:00

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, EmailStr, Field, constr


class Identifier(BaseModel):
    scheme: Optional[str] = 'DOI'
    schemeURI: Optional[str] = ''
    identifier: str = Field(
        ...,
        description="Enter most relevant publication DOI(s). e.g. '10.016/j.epsl.2009.11.018'",
        title='Publication DOI',
    )
    url: Optional[str] = ''


class Identifier1(BaseModel):
    scheme: Optional[str] = 'IGSN'
    schemeURI: Optional[str] = Field('', description='URL of the scheme')
    identifier: str = Field(
        ...,
        description='Provide IGSNs for your samples separated by commas.',
        title='IGSN',
    )
    url: Optional[str] = ''


class Identifier2(BaseModel):
    scheme: Optional[str] = 'SVN'
    schemeURI: Optional[str] = ''
    identifier: str = Field(
        ...,
        description='Provide volcano numbers corresponding to your sample collection site.',
        title='Smithsonian Volcano Number',
    )
    url: Optional[str] = ''


class Identifier3(BaseModel):
    scheme: Optional[str] = 'R2R'
    schemeURI: Optional[str] = ''
    identifier: str = Field(
        ...,
        description='Provide Cruise DOIs corresponding to your samples.',
        title='Cruise DOI',
    )
    url: Optional[str] = ''


class Type(Enum):
    Collection = 'Collection'
    Dataset = 'Dataset'
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


class AdditionalType(Enum):
    Chemistry = 'Chemistry'
    Chemistry_ClumpedIsotope = 'Chemistry:ClumpedIsotope'
    Chemistry_Fluid = 'Chemistry:Fluid'
    Chemistry_Gas = 'Chemistry:Gas'
    Chemistry_Rock = 'Chemistry:Rock'
    Chemistry_Sediment = 'Chemistry:Sediment'
    Geochronology = 'Geochronology'
    Kinetics = 'Kinetics'
    ModelData = 'ModelData'
    Petrography = 'Petrography'
    Petrology = 'Petrology'
    Petrology_Experimental = 'Petrology:Experimental'
    Petrology_Mineral = 'Petrology:Mineral'
    SampleInfo = 'SampleInfo'
    SocialScience = 'SocialScience'
    Other = 'Other'


class Funder(BaseModel):
    alternateName: Optional[str] = None


class Funding(BaseModel):
    identifier: Optional[str] = Field(None, title='Award Number')
    funder: Optional[Funder] = {'alternateName': 'NSF'}
    url: Optional[str] = 'https://ror.org/021nxhr62'


class Funder1(BaseModel):
    alternateName: Optional[str] = None


class Funding1(BaseModel):
    identifier: Optional[str] = Field(None, title='Award Number')
    funder: Optional[Funder1] = {'alternateName': 'SLOAN'}
    url: Optional[str] = 'https://ror.org/052csg198'


class Funder2(BaseModel):
    alternateName: Optional[str] = None


class Funding2(BaseModel):
    identifier: Optional[str] = Field(None, title='Award Number')
    funder: Optional[Funder2] = {'alternateName': 'DOE'}
    url: Optional[str] = 'https://ror.org/01bj3aw27'


class Funder3(BaseModel):
    alternateName: Optional[str] = None


class Funding3(BaseModel):
    identifier: Optional[str] = Field(None, title='Award Number')
    funder: Optional[Funder3] = {'alternateName': 'NASA'}
    url: Optional[str] = 'https://ror.org/027ka1x80'


class Funder4(BaseModel):
    alternateName: Optional[str] = None


class Funding4(BaseModel):
    identifier: Optional[str] = Field(None, title='Award Number')
    funder: Optional[Funder4] = {'alternateName': 'ERC'}
    url: Optional[str] = 'https://ror.org/0472cxd90'


class Funder5(BaseModel):
    alternateName: Optional[str] = None


class Funding5(BaseModel):
    identifier: Optional[str] = Field(None, title='Award Number')
    funder: Optional[Funder5] = {'alternateName': 'DFG'}
    url: Optional[str] = 'https://ror.org/018mejw64'


class Funder6(BaseModel):
    alternateName: Optional[str] = None


class Funding6(BaseModel):
    identifier: Optional[str] = Field(None, title='Award Number')
    funder: Optional[Funder6] = {'alternateName': 'NSFC'}
    url: Optional[str] = 'https://ror.org/01h0zpd94'


class Funder7(BaseModel):
    alternateName: Optional[str] = None


class Funding7(BaseModel):
    identifier: Optional[str] = Field(None, title='Award Number')
    funder: Optional[Funder7] = {'alternateName': 'ARC'}
    url: Optional[str] = 'https://ror.org/05mmh0f86'


class Funder8(BaseModel):
    alternateName: Optional[str] = None


class Funding8(BaseModel):
    identifier: Optional[str] = Field(None, title='Award Number')
    funder: Optional[Funder8] = {'alternateName': 'RSCF'}
    url: Optional[str] = 'https://ror.org/03y2gwe85'


class Funder9(BaseModel):
    alternateName: Optional[str] = None


class Funding9(BaseModel):
    identifier: Optional[str] = Field(None, title='Award Number')
    funder: Optional[Funder9] = {'alternateName': 'NERC'}
    url: Optional[str] = 'https://ror.org/02b5d8509'


class Funder10(BaseModel):
    alternateName: Optional[str] = None


class Funding10(BaseModel):
    identifier: Optional[str] = Field(
        None,
        description='Please enter other funding sources in the format of: Funding Source Name (012345)',
        title='Funding Source',
    )
    funder: Optional[Funder10] = Field(
        {'alternateName': 'Other'},
        description='A person or organization that provides money for a particular purpose',
        title='Funder',
    )


class Cordinate(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    alt: Optional[float] = None


class FileResponse(BaseModel):
    fileName: Optional[str] = None
    message: Optional[str] = None


class Type1(Enum):
    Point = 'Point'
    LineString = 'LineString'
    Polygon = 'Polygon'


class Geometry(BaseModel):
    type: Optional[Type1] = None
    cordinates: Optional[List[Cordinate]] = None


class IdentifierModel(BaseModel):
    scheme: Optional[str] = None
    schemeURI: Optional[str] = None
    identifier: Optional[str] = None
    url: Optional[str] = None


class AuthorIdentifier(BaseModel):
    scheme: Optional[str] = 'ORCID'
    schemeURI: Optional[str] = 'https://orcid.org/'
    identifier: Optional[constr(regex=r'(\d{4}-){3}\d{4}')] = Field(None, title='ORCID')


class LicenseItem(BaseModel):
    alternateName: Optional[str] = 'CC-BY-NC-SA-3.0'


class LicenseItem1(BaseModel):
    alternateName: Optional[str] = 'CC-BY-4.0'


class LicenseItem2(BaseModel):
    alternateName: Optional[str] = 'CC-BY-SA-4.0'


class LicenseItem3(BaseModel):
    alternateName: Optional[str] = 'CC-BY-NC-SA-4.0'


class LicenseItem4(BaseModel):
    alternateName: Optional[str] = 'CC0-1.0'


class License(BaseModel):
    __root__: Union[LicenseItem, LicenseItem1, LicenseItem2, LicenseItem3, LicenseItem4] = Field(..., title='License')


class RecordFile(BaseModel):
    checkum: Optional[str] = None
    description: Optional[str] = None
    format: Optional[str] = None
    name: Optional[str] = None
    position: Optional[int] = None
    serverName: Optional[str] = None
    size: Optional[int] = None
    uploadDate: Optional[str] = None


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


class RelatedResource(BaseModel):
    bibliographicCitation: Optional[str] = None
    identifiers: Optional[List[IdentifierModel]] = None
    relation: Optional[Relation] = None


class Coverage(Enum):
    Global = 'Global'
    Regional__Continents__Oceans_ = 'Regional (Continents, Oceans)'
    Space_Planetary = 'Space/Planetary'


class SpatialCoverage(BaseModel):
    coverage: Coverage = Field(..., title='Spatial Coverage')
    keywords: Optional[List[str]] = Field(
        None,
        description='Provide appropriate geographic keywords for searches. (e.g. Pacific Ocean, Aleutian Islands)',
        title='Geographic Keywords',
    )


class Affiliation(BaseModel):
    name: Optional[str] = None
    identifiers: Optional[List[IdentifierModel]] = None


class Contributor(BaseModel):
    givenName: str = Field(..., title='First Name')
    additionalName: Optional[str] = Field(None, title='Middle Name')
    familyName: str = Field(..., title='Last Name')
    email: Optional[EmailStr] = None
    identifiers: Optional[List[AuthorIdentifier]] = None


class LeadAuthor(BaseModel):
    givenName: str = Field(..., title='First Name')
    additionalName: Optional[str] = Field(None, title='Middle Name')
    familyName: str = Field(..., title='Last Name')
    email: EmailStr
    identifiers: Optional[List[AuthorIdentifier]] = None


class Feature(BaseModel):
    type: Optional[str] = None
    geometry: Optional[Geometry] = None


class Record(BaseModel):
    title: str = Field(..., description='A descriptive title of the dataset', title='Dataset Title')
    datePublished: date = Field(
        ...,
        description='The date of the files contained in the resource to be allowed for downloading',
        title='Release Date',
    )
    description: constr(max_length=250) = Field(
        ...,
        description='Describe measurements, location, and purpose of the dataset',
        title='Abstract or Description',
    )
    community: str = Field(..., title='Community')
    identifiers: Optional[List[Union[Identifier, Identifier1, Identifier2, Identifier3]]] = Field(
        None, title='Related Information'
    )
    leadAuthor: Optional[LeadAuthor] = None
    creators: Optional[List[Contributor]] = Field(None, max_items=3, title='Co-Authors')
    type: Type = Field(..., description='The nature or genre of the resource', title='Dataset Type')
    status: Status = Field(
        ...,
        description='Indication of the progress status of the resource.',
        title='Submission status',
    )
    additionalTypes: List[AdditionalType] = Field(
        ...,
        description='The science domain of the content',
        title='Data Types',
        unique_items=True,
    )
    keywords: List[str] = Field(
        ...,
        description='A list of non-geographic keywords. (e.g. volatiles, ultra-slow spreading ridges, mantle melting, CO2 fluxes)',
        min_items=2,
        title='Keywords',
    )
    language: Optional[str] = None
    spatialCoverage: SpatialCoverage
    relatedResources: Optional[List[RelatedResource]] = None
    fundings: Optional[
        List[
            Union[
                Union[
                    Funding,
                    Funding1,
                    Funding2,
                    Funding3,
                    Funding4,
                    Funding5,
                    Funding6,
                    Funding7,
                    Funding8,
                    Funding9,
                ],
                Funding10,
            ]
        ]
    ] = Field(
        None,
        description='Source of grants/awards which have funded the resource',
        title='Funding Source',
    )
    license: Optional[License] = None
