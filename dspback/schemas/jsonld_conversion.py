from geojson import Feature, Point

from dspback.schemas.earthchem.model import Record
from dspback.schemas.hydroshare.model import ResourceMetadata


def hs_convert_to_jsonld(metadata: ResourceMetadata):
    def to_geojson(sc):
        if hasattr(sc, 'northlimit'):
            return [sc.northlimit, sc.southlimit, sc.eastlimit, sc.westlimit]
        else:
            return Feature(geometry=Point([float(sc.east), float(sc.north)]))
        pass

    def to_funder(f):
        return {
            '@type': 'Grant',
            'identifier': f.number,
            'name': f.title,
            'funder': {'@type': 'Organization', 'name': f.funding_agency_name, 'identifier': f.funding_agency_url},
        }

    return {
        '@type': 'Dataset',
        'provider': {'name': "HydroShare"},
        'name': metadata.title,
        'description': metadata.abstract,
        'keywords': metadata.subjects,
        'temporalCoverage': {'start': metadata.period_coverage.start, 'end': metadata.period_coverage.end},
        'spatialCoverage': {'geojson': [to_geojson(metadata.spatial_coverage)]},
        'creator': {'@list': [{'name': creator.name} for creator in metadata.creators]},
        'license': {'@type': 'CreativeWork', 'text': metadata.rights.statement, 'url': metadata.rights.url},
        'funding': [to_funder(award) for award in metadata.awards],
        # not in the json metadata
        'datePublished': None,
    }


def ecl_convert_to_jsonld(metadata: Record):
    def to_name(author):
        name = ''
        if author.givenName:
            name = author.givenName + ' '
        if author.additionalName:
            name = name + author.additionalName + ' '
        if author.familyName:
            name = name + author.familyName
        return name.strip()

    return {
        '@type': 'Dataset',
        'provider': {'name': "EarthChem Library"},
        'name': metadata.title,
        'description': metadata.description,
        'keywords': metadata.keywords,
        'creator': {
            '@list': [{'name': to_name(contributor)} for contributor in metadata.leadAuthor + metadata.contributors]
        },
        'license': {'@type': 'CreativeWork', 'url': metadata.license},
        'datePublished': metadata.datePublished,
        #'temporalCoverage': {'start': metadata.period_coverage.start,
        #                     'end': metadata.period_coverage.end},
        #'spatialCoverage': {'geojson': [to_geojson(metadata.spatial_coverage)]},
    }
