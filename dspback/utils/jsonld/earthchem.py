import json

from bs4 import BeautifulSoup

from dspback.utils.jsonld.formatter import format_fields


def scrape_jsonld(resource_data):
    resource_soup = BeautifulSoup(resource_data, "html.parser")
    resource_json_ld = resource_soup.find("script", {"type": "application/ld+json"})
    resource_json_ld = json.loads(resource_json_ld.text)
    resource_json_ld = format_fields(resource_json_ld)

    return resource_json_ld
