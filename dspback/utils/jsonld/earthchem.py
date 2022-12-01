import json
import re

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
    if "datePublished" in json_ld["distribution"]:
        json_ld["datePublished"] = dateutil.parser.isoparse(json_ld["distribution"]["datePublished"])
        json_ld["distribution"]["datePublished"] = dateutil.parser.isoparse(json_ld["distribution"]["datePublished"])

    # format spatial coverage
    if "spatialCoverage" in json_ld:
        spatial_coverage = json_ld["spatialCoverage"]
        spatial_coverage_geo = spatial_coverage["geo"]
        spatial_coverage["geojson"] = []
        for sc in spatial_coverage_geo:
            if sc["@type"] == "GeoCoordinates":
                point = Feature(geometry=Point([float(sc["longitude"]), float(sc["latitude"])]))
                spatial_coverage["geojson"].append(point)
            if sc["@type"] == "GeoShape":
                south, west, north, east = sc["box"].split(" ")
                bbox = [float(north), float(south), float(east), float(west)]
                spatial_coverage["geojson"].append(bbox)

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
            json_ld["keywords"] = re.split(r',(?=[^/s ])', json_ld["keywords"])

    return json_ld


def scrape_jsonld(resource_data):
    resource_soup = BeautifulSoup(resource_data, "html.parser")
    resource_json_ld = resource_soup.find("script", {"type": "application/ld+json"})
    resource_json_ld = json.loads(resource_json_ld.text)
    resource_json_ld = _format_fields(resource_json_ld)
    resource_json_ld["clusters"] = _clusters(resource_json_ld)

    return resource_json_ld
