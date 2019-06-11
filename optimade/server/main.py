import urllib
from datetime import datetime

from fastapi import FastAPI, Depends
from pymongo import MongoClient
from starlette.requests import Request

from .deps import EntryListingQueryParams
from .collections import MongoCollection
from .models import (
    Link, Links, StructureResource, OptimadeResponseMeta, OptimadeResponseMetaQuery,
    OptimadeStructureResponse,
)

app = FastAPI(
    title=" OPTiMaDe API",
    description=("The [Open Databases Integration for Materials Design (OPTiMaDe) consortium]"
                 "(http://http://www.optimade.org/) aims to make materials databases interoperational"
                 " by developing a common REST API."),
    version="0.9",
)

client = MongoClient()
structures = MongoCollection(client.optimade.structures, StructureResource)


@app.get("/structures", response_model=OptimadeStructureResponse, response_model_skip_defaults=True, tags=['Structure'])
def get_structures(request: Request, params: EntryListingQueryParams = Depends()):
    results, more_data_available, data_available = structures.find(params)
    parse_result = urllib.parse.urlparse(str(request.url))
    if more_data_available:
        query = urllib.parse.parse_qs(parse_result.query)
        query['page[offset]'] = int(query.get('page[offset]', '[0]')[0]) + len(results)
        urlencoded = urllib.parse.urlencode(query, doseq=True)
        links = Links(next=Link(href=f'{parse_result.scheme}://{parse_result.netloc}{parse_result.path}?{urlencoded}'))
    else:
        links = Links(next=None)

    meta = OptimadeResponseMeta(
        query=OptimadeResponseMetaQuery(
            representation=f'{parse_result.path}?{parse_result.query}'),
        api_version='v0.9',
        time_stamp=datetime.utcnow(),
        data_returned=len(results),
        more_data_available=more_data_available,
    )
    return OptimadeStructureResponse(
        links=links,
        data=results,
        meta=meta,
    )
