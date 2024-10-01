import html
import json

import aiohttp
from bs4 import BeautifulSoup

from dspback.pydantic_schemas import RepositoryType
from dspback.schemas.discovery import JSONLD
from dspback.utils.jsonld.formatter import format_fields


def scrape_jsonld(resource_data, script_match):
    resource_soup = BeautifulSoup(resource_data, "html.parser")
    resource_json_ld = resource_soup.find("script", script_match)
    if resource_json_ld:
        resource_json_ld = json.loads(html.unescape(resource_json_ld.text))
        resource_json_ld = format_fields(resource_json_ld)

    return resource_json_ld


async def fetch_landing_page(url):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            return await response.text()


async def retrieve_discovery_jsonld(identifier, repository_type, url):
    resource_data = await fetch_landing_page(url)
    if not resource_data:
        return None
    script_match = (
        {"id": "schemaorg"} if repository_type == RepositoryType.HYDROSHARE else {"type": "application/ld+json"}
    )
    resource_json_ld = scrape_jsonld(resource_data, script_match=script_match)
    if not resource_json_ld:
        return None
    if repository_type == RepositoryType.HYDROSHARE and resource_json_ld["creativeWorkStatus"] == "Private":
        return None

    # only Zenodo does not have provider in the json ld
    if repository_type == RepositoryType.ZENODO:
        resource_json_ld['provider'] = {'name': 'Zenodo'}
        parse_funding_jsonld(resource_json_ld)

    resource_json_ld["repository_identifier"] = identifier
    jsonld = JSONLD(**resource_json_ld)
    return jsonld.dict(by_alias=True, exclude_none=True)


def parse_funding_jsonld(resource_json_ld):
    if 'funding' in resource_json_ld:
        funding_items = resource_json_ld['funding']
        all_funding = []
        for funder_item in funding_items:
            funder_name = funder_item['funder']['name']
            identifier = funder_item['identifier'].split('::')[1]
            funding_name = funder_item['name']
            all_funding.append({'name': funding_name, 'identifier': identifier, 'funder': {'name': funder_name}})
        resource_json_ld['funding'] = all_funding
