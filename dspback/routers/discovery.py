import functools
import json
from datetime import datetime

import pandas
from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse

from dspback.config import get_settings
from dspback.schemas.discovery import DiscoveryResult, PathEnum, TypeAhead

router = APIRouter()


@router.get(
    "/search",
    response_model_exclude_none=True,
    response_model_by_alias=True,
    response_model=list[DiscoveryResult],
)
async def search(
    request: Request,
    term: str,
    sortBy: str = None,
    contentType: str = None,
    providerName: str = None,
    creatorName: str = None,
    dataCoverageStart: int = None,
    dataCoverageEnd: int = None,
    publishedStart: int = None,
    publishedEnd: int = None,
    clusters: list[str] | None = Query(default=None),
    pageNumber: int = 1,
    pageSize: int = 30,
):
    search_paths = PathEnum.values()

    should = [{'autocomplete': {'query': term, 'path': key, 'fuzzy': {'maxEdits': 1}}} for key in search_paths]
    must = []
    stages = []
    filters = []

    if publishedStart:
        filters.append(
            {
                'range': {
                    'path': 'datePublished',
                    'gte': datetime(publishedStart, 1, 1),
                },
            }
        )

    if publishedEnd:
        filters.append(
            {
                'range': {
                    'path': 'datePublished',
                    'lt': datetime(publishedEnd + 1, 1, 1),  # +1 to include all of the publishedEnd year
                },
            }
        )

    if dataCoverageStart:
        filters.append({'range': {'path': 'temporalCoverage.start', 'gte': datetime(dataCoverageStart, 1, 1)}})

    if dataCoverageEnd:
        filters.append({'range': {'path': 'temporalCoverage.end', 'lt': datetime(dataCoverageEnd + 1, 1, 1)}})

    if creatorName:
        must.append({'text': {'path': 'creator.@list.name', 'query': creatorName}})

    if providerName:
        must.append({'text': {'path': 'provider.name', 'query': providerName}})

    if contentType:
        must.append({'text': {'path': '@type', 'query': contentType}})

    stages.append(
        {
            '$search': {
                'index': 'fuzzy_search',
                'compound': {'filter': filters, 'should': should, 'must': must, 'minimumShouldMatch': 1},
                'highlight': {'path': search_paths}
            }
        }
    )

    if clusters:
        stages.append({'$match': {'clusters': {'$all': clusters}}})

    # Sort needs to happen before pagination
    if sortBy:
        stages.append({'$sort': {sortBy: 1}})

    stages.append({'$skip': (pageNumber - 1) * pageSize})
    stages.append(
        {'$limit': pageSize},
    )
    stages.append({'$unset': ['_id']})
    stages.append(
        {'$set': {'score': {'$meta': 'searchScore'}, 'highlights': {'$meta': 'searchHighlights'}}},
    )

    result = await request.app.db[get_settings().mongo_database]["discovery"].aggregate(stages).to_list(pageSize)
    return result


@router.get("/typeahead", response_model=list[TypeAhead])
async def typeahead(request: Request, term: str, pageSize: int = 30):
    search_terms = PathEnum.values()

    should = [{'autocomplete': {'query': term, 'path': key, 'fuzzy': {'maxEdits': 1}}} for key in search_terms]

    project = {term: 1 for term in search_terms}
    project["highlights"] = {'$meta': 'searchHighlights'}
    project["_id"] = 0
    project["name"] = 0
    project["description"] = 0
    project["keywords"] = 0
    project["creator.@list.name"] = 0

    stages = [
        {
            '$search': {
                'index': 'fuzzy_search',
                'compound': {'should': should},
                'highlight': {'path': search_terms},
            }
        },
        {'$project': project},
    ]
    result = await request.app.db[get_settings().mongo_database]["typeahead"].aggregate(stages).to_list(pageSize)
    return result


@router.get("/creators")
async def creator_search(request: Request, name: str, pageSize: int = 30) -> list[str]:
    stages = [
        {
            '$search': {
                'index': 'fuzzy_search',
                'autocomplete': {"query": name, "path": "creator.@list.name", 'fuzzy': {'maxEdits': 1}},
                'highlight': {'path': 'creator.@list.name'},
            }
        },
        {'$project': {"_id": 0, "creator.@list.name": 1, "highlights": {'$meta': 'searchHighlights'}}},
    ]

    results = await request.app.db[get_settings().mongo_database]["discovery"].aggregate(stages).to_list(pageSize)

    names = []
    for result in results:
        for highlight in result['highlights']:
            for text in highlight['texts']:
                if text['type'] == 'hit':
                    for creator in result['creator']['@list']:
                        if text['value'] in creator['name']:
                            names.append(creator['name'])

    return set(names)


@router.get("/csv")
async def csv(request: Request):
    project = [{'$project': {'name': 1, 'description': 1, 'keywords': 1, '_id': 0}}]
    json_response = await request.app.db[get_settings().mongo_database]["discovery"].aggregate(project).to_list(None)
    df = pandas.read_json(json.dumps(json_response))
    filename = "file.csv"
    df.to_csv(filename)
    return FileResponse(filename, filename=filename, media_type='application/octet-stream')


def compare(c1: str, c2: str):
    if c1.startswith("CZO"):
        if c2.startswith("CZO"):
            return c1 < c2
        else:
            return 1
    if c2.startswith("CZO"):
        return -1
    return c1 < c2


@router.get("/clusters")
async def clusters(request: Request) -> list[str]:
    existing_clusters = await request.app.db[get_settings().mongo_database]["discovery"].find().distinct('clusters')
    return sorted(existing_clusters, key=functools.cmp_to_key(compare))
