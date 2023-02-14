import dateutil.parser
from geojson import Feature, Point

from dspback.utils.jsonld.clusters import clusters


def format_fields(json_ld):
    # format datetime fields
    if "dateCreated" in json_ld:
        json_ld["dateCreated"] = dateutil.parser.isoparse(json_ld["dateCreated"])
    if "dateModified" in json_ld:
        json_ld["dateModified"] = dateutil.parser.isoparse(json_ld["dateModified"])
    if "datePublished" in json_ld:
        json_ld["datePublished"] = dateutil.parser.isoparse(json_ld["datePublished"])
    # earthchem keeps datePublished in distribution
    if "distribution" in json_ld:
        if "datePublished" in json_ld["distribution"]:
            json_ld["datePublished"] = dateutil.parser.isoparse(json_ld["distribution"]["datePublished"])
            json_ld["distribution"]["datePublished"] = dateutil.parser.isoparse(
                json_ld["distribution"]["datePublished"]
            )

    # format spatial coverage
    if "spatialCoverage" in json_ld:
        spatial_coverage = json_ld["spatialCoverage"]
        spatial_coverage_geo = (
            spatial_coverage["geo"] if isinstance(spatial_coverage["geo"], list) else [spatial_coverage["geo"]]
        )
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

    if "funding" in json_ld:
        for funding in json_ld["funding"]:
            if "funder" in funding:
                if not isinstance(funding["funder"], list):
                    funding["funder"] = [funding["funder"]]

    if "creator" in json_ld:
        if isinstance(json_ld["creator"], list):
            creators = json_ld["creator"]
            json_ld["creator"] = {'@list': creators}

    if "license" in json_ld:
        if isinstance(json_ld["license"], str):
            json_ld["license"] = {"text": json_ld["license"]}

    if "author" in json_ld:
        for author_role in [author_list['author'] for author_list in json_ld['author']['@list']]:
            json_ld["creator"] = {'@list': author_role}

    json_ld["clusters"] = clusters(json_ld)

    return json_ld
