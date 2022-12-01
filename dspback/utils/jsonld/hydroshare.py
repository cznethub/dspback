import json

import dateutil.parser
from bs4 import BeautifulSoup
from geojson import Feature, Point

from dspback.utils.jsonld.clusters import _clusters


def _format_fields(json_ld):
    # format datetime fields
    if "dateCreated" in json_ld:
        json_ld["dateCreated"] = dateutil.parser.isoparse(json_ld["dateCreated"])
    if "dateModified" in json_ld:
        json_ld["dateModified"] = dateutil.parser.isoparse(json_ld["dateModified"])
    if "datePublished" in json_ld:
        json_ld["datePublished"] = dateutil.parser.isoparse(json_ld["datePublished"])

    # format spatial coverage
    if "spatialCoverage" in json_ld:
        spatial_coverage = json_ld["spatialCoverage"]
        spatial_coverage_geo = spatial_coverage["geo"]
        if spatial_coverage_geo["@type"] == "GeoCoordinates":
            point = Feature(
                geometry=Point([float(spatial_coverage_geo["longitude"]), float(spatial_coverage_geo["latitude"])])
            )
            spatial_coverage["geojson"] = [point]
        if spatial_coverage_geo["@type"] == "GeoShape":
            south, west, north, east = spatial_coverage_geo["box"].split(" ")
            bbox = [float(north), float(south), float(east), float(west)]
            spatial_coverage["geojson"] = [bbox]

    # format temporal coverage
    if "temporalCoverage" in json_ld:
        start, end = json_ld["temporalCoverage"].split("/")
        start_date = dateutil.parser.parse(start)
        end_date = dateutil.parser.parse(end)
        json_ld["temporalCoverage"] = {"start": start_date, "end": end_date}

    if "keywords" in json_ld:
        if json_ld["keywords"] is None:
            json_ld["keywords"] = []
        if isinstance(json_ld["keywords"], str):
            json_ld["keywords"] = json_ld["keywords"].split(",")

    return json_ld


def scrape_jsonld(resource_data):
    resource_soup = BeautifulSoup(resource_data, "html.parser")
    resource_json_ld = resource_soup.find("script", {"id": "schemaorg"})
    resource_json_ld = json.loads(resource_json_ld.text)
    resource_json_ld = _format_fields(resource_json_ld)
    resource_json_ld["clusters"] = _clusters(resource_json_ld)

    return resource_json_ld
