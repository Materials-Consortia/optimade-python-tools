import urllib
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path
from typing import Union

from fastapi import FastAPI, Depends
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from .deps import EntryListingQueryParams
from .collections import MongoCollection
from .models.jsonapi import Link, ToplevelLinks
from .models.optimade_json import Error
from .models.structures import StructureResource, StructureResourceAttributes
from .models.entries import EntryInfoResource
from .models.baseinfo import BaseInfoResource, BaseInfoAttributes
from .models.toplevel import (
    ResponseMeta,
    ResponseMetaQuery,
    StructureResponseMany,
    InfoResponse,
    Provider,
    ErrorResponse,
    EntryInfoResponse,
)

config = ConfigParser()
config.read(Path(__file__).resolve().parent.joinpath("config.ini"))
USE_REAL_MONGO = config["DEFAULT"].getboolean("USE_REAL_MONGO")

app = FastAPI(
    title="OPTiMaDe API",
    description=(
        "The [Open Databases Integration for Materials Design (OPTiMaDe) consortium]"
        "(http://http://www.optimade.org/) aims to make materials databases interoperational "
        "by developing a common REST API."
    ),
    version="0.10.0",
)


if USE_REAL_MONGO:
    from pymongo import MongoClient
else:
    from mongomock import MongoClient

client = MongoClient()
structures = MongoCollection(
    client.optimade.structures, StructureResource, StructureResourceAttributes
)

test_structures_path = (
    Path(__file__).resolve().parent.joinpath("tests/test_more_structures.json")
)
if not USE_REAL_MONGO and test_structures_path.exists():
    import json
    import bson.json_util

    print("loading test structures...")
    with open(test_structures_path) as f:
        data = json.load(f)
        print("inserting test structures into collection...")
        structures.collection.insert_many(
            bson.json_util.loads(bson.json_util.dumps(data))
        )
    print("done inserting test structures...")


def meta_values(url, data_returned, data_available, more_data_available=False):
    """Helper to initialize the meta values"""
    parse_result = urllib.parse.urlparse(url)
    return ResponseMeta(
        query=ResponseMetaQuery(
            representation=f"{parse_result.path}?{parse_result.query}"
        ),
        api_version="v0.10",
        time_stamp=datetime.utcnow(),
        data_returned=data_returned,
        more_data_available=more_data_available,
        provider=Provider(
            name="test",
            description="A test database provider",
            prefix="exmpl",
            homepage=None,
            index_base_url=None,
        ),
        data_available=data_available,
    )


def update_schema(app):
    """Update OpenAPI schema in file 'local_openapi.json'"""
    with open("local_openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=2)


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            ErrorResponse(
                meta=meta_values(str(request.url), 0, 0, False),
                errors=[Error(detail=exc.detail, code=exc.status_code)],
            ),
            skip_defaults=True,
        ),
    )


@app.get(
    "/structures",
    response_model=Union[StructureResponseMany, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Structure"],
)
def get_structures(request: Request, params: EntryListingQueryParams = Depends()):
    results, more_data_available, data_available = structures.find(params)
    parse_result = urllib.parse.urlparse(str(request.url))
    if more_data_available:
        query = urllib.parse.parse_qs(parse_result.query)
        query["page_offset"] = int(query.get("page_offset", [0])[0]) + len(results)
        urlencoded = urllib.parse.urlencode(query, doseq=True)
        links = ToplevelLinks(
            next=Link(
                href=f"{parse_result.scheme}://{parse_result.netloc}{parse_result.path}?{urlencoded}"
            )
        )
    else:
        links = ToplevelLinks(next=None)
    return StructureResponseMany(
        links=links,
        data=results,
        meta=meta_values(
            str(request.url), len(results), data_available, more_data_available
        ),
    )


@app.get(
    "/info",
    response_model=Union[InfoResponse, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Info"],
)
def get_info(request: Request):
    return InfoResponse(
        meta=meta_values(str(request.url), 1, 1, more_data_available=False),
        data=BaseInfoResource(
            attributes=BaseInfoAttributes(
                api_version="v0.10",
                available_api_versions=[
                    {"url": "http://localhost:5000/", "version": "0.10.0"}
                ],
                entry_types_by_format={"json": ["structures"]},
                available_endpoints=["info", "structures"],
            )
        ),
    )


@app.get(
    "/info/structures",
    response_model=Union[EntryInfoResponse, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Structure", "Info"],
)
def get_structures_info(request: Request):
    schema_properties = StructureResourceAttributes.schema().get("properties")

    output_fields_by_format = {"json": ["id", "type"]}
    output_fields_by_format["json"].extend(schema_properties.keys())

    properties = {}
    for key, key_info in schema_properties.items():
        properties[key] = {}
        for info in key_info:
            if info in {"description", "unit"}:
                properties[key][info] = key_info[info]
    for key, key_info in StructureResource.schema().get("properties").items():
        if key in {"id", "type"}:
            properties[key] = {}
            for info in key_info:
                if info in {"description", "unit"}:
                    properties[key][info] = key_info[info]

    return EntryInfoResponse(
        meta=meta_values(str(request.url), 1, 1, more_data_available=False),
        data=EntryInfoResource(
            formats=list(output_fields_by_format.keys()),
            description="Materials structure entries",
            properties=properties,
            output_fields_by_format=output_fields_by_format,
        ),
    )


@app.on_event("startup")
async def startup_event():
    update_schema(app)
