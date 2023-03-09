import json
from datetime import datetime

import pandas
from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse

from dspback.config import get_settings

router = APIRouter()


@router.get("/search")
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
    searchPaths = ['name', 'description', 'keywords']
    highlightPaths = ['name', 'description', 'keywords', 'creator.@list.name']
    autoCompletePaths = ['name', 'description', 'keywords']

    should = [{'autocomplete': {'query': term, 'path': key, 'fuzzy': {'maxEdits': 1}}} for key in autoCompletePaths]
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
                'compound': {'filter': filters, 'should': should, 'must': must},
                'highlight': {'path': highlightPaths},
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


@router.get("/typeahead")
async def typeahead(request: Request, term: str, pageSize: int = 30):
    autoCompletePaths = ['name', 'description', 'keywords']
    highlightsPaths = ['name', 'description', 'keywords']
    should = [{'autocomplete': {'query': term, 'path': key, 'fuzzy': {'maxEdits': 1}}} for key in autoCompletePaths]

    stages = [
        {
            '$search': {
                'index': 'fuzzy_search',
                'compound': {
                    'should': [
                        {'autocomplete': {'query': term, 'path': 'description', 'fuzzy': {'maxEdits': 1}}},
                        {'autocomplete': {'query': term, 'path': 'name', 'fuzzy': {'maxEdits': 1}}},
                        {'autocomplete': {'query': term, 'path': 'keywords', 'fuzzy': {'maxEdits': 1}}},
                    ]
                },
                'highlight': {'path': ['description', 'name', 'keywords']},
            }
        },
        {
            '$project': {
                'name': 1,
                'description': 1,
                'keywords': 1,
                'highlights': {'$meta': 'searchHighlights'},
                '_id': 0,
            }
        },
    ]
    result = await request.app.db[get_settings().mongo_database]["discovery"].aggregate(stages).to_list(pageSize)
    return result


@router.get("/csv")
async def csv(request: Request):
    project = [{'$project': {'name': 1, 'description': 1, 'keywords': 1, '_id': 0}}]
    json_response = await request.app.db[get_settings().mongo_database]["discovery"].aggregate(project).to_list(None)
    df = pandas.read_json(json.dumps(json_response))
    filename = "file.csv"
    df.to_csv(filename)
    return FileResponse(filename, filename=filename, media_type='application/octet-stream')


@router.get("/clusters")
async def clusters(request: Request):
    return await request.app.db[get_settings().mongo_database]["discovery"].find().distinct('clusters')
