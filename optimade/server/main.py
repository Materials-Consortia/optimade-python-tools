import urllib
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Depends
from starlette.requests import Request

from .deps import EntryListingQueryParams
from .collections import MongoCollection
from .models.jsonapi import Link, Links
from .models.structures import StructureResource
from .models.baseinfo import BaseInfoResource, BaseInfoAttributes
from .models.toplevel import OptimadeResponseMeta, OptimadeResponseMetaQuery, OptimadeStructureResponseMany, OptimadeInfoResponse, OptimadeProvider


config = ConfigParser()
config.read(Path(__file__).resolve().parent.joinpath('config.ini'))
USE_REAL_MONGO = config['DEFAULT'].getboolean('USE_REAL_MONGO')

app = FastAPI(
    title=" OPTiMaDe API",
    description=("The [Open Databases Integration for Materials Design (OPTiMaDe) consortium]"
                 "(http://http://www.optimade.org/) aims to make materials databases interoperational"
                 " by developing a common REST API."),
    version="0.9",
)


if USE_REAL_MONGO:
    from pymongo import MongoClient
else:
    from mongomock import MongoClient

client = MongoClient()
structures = MongoCollection(client.optimade.structures, StructureResource)

test_structures_path = Path(__file__).resolve().parent.joinpath('test_structures.json')
if not USE_REAL_MONGO and test_structures_path.exists():
    import json
    import bson.json_util
    print('loading test structures...')
    with open(test_structures_path) as f:
        data = json.load(f)
        print('inserting test structures into collection...')
        structures.collection.insert_many(bson.json_util.loads(bson.json_util.dumps(data)))
    print('done inserting test structures...')


def meta_values(url,data_returned, more_data_available=False):
    """Helper to initialize the meta values"""
    parse_result = urllib.parse.urlparse(url)
    return OptimadeResponseMeta(
        query=OptimadeResponseMetaQuery(
            representation=f'{parse_result.path}?{parse_result.query}'),
        api_version='v0.9',
        time_stamp=datetime.utcnow(),
        data_returned=data_returned,
        more_data_available=more_data_available,
        provider=OptimadeProvider(
            name="test",
            description="A test database provider",
            prefix="tst",
            homepage=None,
            index_base_url=None)
    )


@app.get("/structures", response_model=OptimadeStructureResponseMany, response_model_skip_defaults=True, tags=['Structure'])
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
    return OptimadeStructureResponseMany(
        links=links,
        data=results,
        meta=meta_values(str(request.url), len(results), more_data_available),
    )

@app.get("/info", response_model=OptimadeInfoResponse, response_model_skip_defaults=True, tags=['Structure'])
def get_info(request: Request, params: EntryListingQueryParams = Depends()):
    return OptimadeInfoResponse(
        meta=meta_values(str(request.url), 1, more_data_available=False),
        data=BaseInfoResource(attributes=BaseInfoAttributes(
                api_version='v0.9',
                available_api_versions={'v0.9': 'http://localhost:5000/'},
                entry_types_by_format={ 'json': ['structures'] }
            ))
    )

@app.on_event("startup")
async def startup_event():
    with open('local_openapi.json', 'w') as f:
        json.dump(app.openapi(), f, indent=2)
