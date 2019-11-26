import json
from pathlib import Path
from typing import Union

from pydantic import ValidationError
from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from optimade.models import (
    StructureResource,
    ReferenceResource,
    InfoResponse,
    ErrorResponse,
    EntryInfoResponse,
    ReferenceResponseMany,
    ReferenceResponseOne,
    StructureResponseMany,
    StructureResponseOne,
)

from .deps import EntryListingQueryParams, SingleEntryQueryParams
from .entry_collections import MongoCollection
from .config import CONFIG
from .mappers import StructureMapper, ReferenceMapper
import optimade.server.utils as u


app = FastAPI(
    title="OPTiMaDe API",
    description=(
        "The [Open Databases Integration for Materials Design (OPTiMaDe) consortium]"
        "(http://http://www.optimade.org/) aims to make materials databases interoperational "
        "by developing a common REST API."
    ),
    version="0.10.0",
)


if CONFIG.use_real_mongo:
    from pymongo import MongoClient
else:
    from mongomock import MongoClient

client = MongoClient()
structures = MongoCollection(
    client[CONFIG.mongo_database]["structures"], StructureResource, StructureMapper
)
references = MongoCollection(
    client[CONFIG.mongo_database]["references"], ReferenceResource, ReferenceMapper
)
entry_collections = {"references": references, "structures": structures}

test_paths = {
    "structures": Path(__file__)
    .resolve()
    .parent.joinpath("tests/test_structures.json"),
    "references": Path(__file__)
    .resolve()
    .parent.joinpath("tests/test_references.json"),
}
if not CONFIG.use_real_mongo and (path.exists() for path in test_paths.values()):
    import bson.json_util

    def load_entries(endpoint_name: str, endpoint_collection: MongoCollection):
        print(f"loading test {endpoint_name}...")
        with open(test_paths[endpoint_name]) as f:
            data = json.load(f)
            print(f"inserting test {endpoint_name} into collection...")
            endpoint_collection.collection.insert_many(
                bson.json_util.loads(bson.json_util.dumps(data))
            )
        print(f"done inserting test {endpoint_name}...")

    load_entries("structures", structures)
    load_entries("references", references)


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return u.general_exception(request, exc)


@app.exception_handler(RequestValidationError)
def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    return u.general_exception(request, exc)


@app.exception_handler(ValidationError)
def validation_exception_handler(request: Request, exc: ValidationError):
    from optimade.models import Error, ErrorSource

    status = 500
    title = "ValidationError"
    errors = []
    for error in exc.errors():
        pointer = "/" + "/".join([str(_) for _ in error["loc"]])
        source = ErrorSource(pointer=pointer)
        code = error["type"]
        detail = error["msg"]
        errors.append(
            Error(detail=detail, status=status, title=title, source=source, code=code)
        )
    return u.general_exception(request, exc, status_code=status, errors=errors)


@app.exception_handler(Exception)
def general_exception_handler(request: Request, exc: Exception):
    return u.general_exception(request, exc)


@app.get(
    "/structures",
    response_model=Union[StructureResponseMany, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Structure"],
)
def get_structures(request: Request, params: EntryListingQueryParams = Depends()):
    return u.get_entries(
        structures, StructureResponseMany, request, params, entry_collections
    )


@app.get(
    "/structures/{entry_id:path}",
    response_model=Union[StructureResponseOne, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Structure"],
)
def get_single_structure(
    request: Request, entry_id: str, params: SingleEntryQueryParams = Depends()
):
    return u.get_single_entry(
        structures, entry_id, StructureResponseOne, request, params, entry_collections
    )


@app.get(
    "/references",
    response_model=Union[ReferenceResponseMany, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Reference"],
)
def get_references(request: Request, params: EntryListingQueryParams = Depends()):
    return u.get_entries(
        references, ReferenceResponseMany, request, params, entry_collections
    )


@app.get(
    "/references/{entry_id:path}",
    response_model=Union[ReferenceResponseOne, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Reference"],
)
def get_single_reference(
    request: Request, entry_id: str, params: SingleEntryQueryParams = Depends()
):
    return u.get_single_entry(
        references, entry_id, ReferenceResponseOne, request, params, entry_collections
    )


@app.get(
    "/info",
    response_model=Union[InfoResponse, ErrorResponse],
    response_model_skip_defaults=False,
    tags=["Info"],
)
def get_info(request: Request):
    from optimade.models import BaseInfoResource, BaseInfoAttributes

    return InfoResponse(
        meta=u.meta_values(str(request.url), 1, 1, more_data_available=False),
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
    "/info/{entry}",
    response_model=Union[EntryInfoResponse, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Info", "Structure", "Reference"],
)
def get_entry_info(request: Request, entry: str):
    from optimade.models import EntryInfoResource

    valid_entry_info_endpoints = {"references", "structures"}
    if entry not in valid_entry_info_endpoints:
        raise StarletteHTTPException(
            status_code=404,
            detail=f"Entry info not found for {entry}, valid entry info endpoints are: {valid_entry_info_endpoints}",
        )

    schema = u.ENTRY_INFO_SCHEMAS[entry]()
    queryable_properties = {"id", "type", "attributes"}
    properties = u.retrieve_queryable_properties(schema, queryable_properties)

    output_fields_by_format = {"json": list(properties.keys())}

    return EntryInfoResponse(
        meta=u.meta_values(str(request.url), 1, 1, more_data_available=False),
        data=EntryInfoResource(
            formats=list(output_fields_by_format.keys()),
            description=schema.get("description", "Entry Resources"),
            properties=properties,
            output_fields_by_format=output_fields_by_format,
        ),
    )


def update_schema(app):
    """Update OpenAPI schema in file 'local_openapi.json'"""
    with open("local_openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=2)


@app.on_event("startup")
async def startup_event():
    update_schema(app)
