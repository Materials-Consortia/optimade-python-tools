import urllib

# from configparser import ConfigParser
from datetime import datetime
from pathlib import Path
from typing import Union, Dict
import json

from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage

from fastapi import FastAPI, Depends
from starlette.requests import Request

from optimade.server.deps import EntryListingQueryParams, EntryInfoQueryParams
from optimade.server.models.jsonapi import Link
from optimade.server.models.modified_jsonapi import Links
from optimade.server.models.structures import StructureResource
from optimade.server.models.entries import (
    EntryInfoAttributes,
    EntryPropertyInfo,
    EntryInfoResource,
)
from optimade.server.models.baseinfo import BaseInfoResource, BaseInfoAttributes
from optimade.server.models.toplevel import (
    ResponseMeta,
    ResponseMetaQuery,
    StructureResponseMany,
    StructureResponseOne,
    InfoResponse,
    Provider,
    ErrorResponse,
    EntryInfoResponse,
)

# config = ConfigParser()
# config.read(Path(__file__).resolve().parent.joinpath("config.ini"))
# USE_REAL_MONGO = config["DEFAULT"].getboolean("USE_REAL_MONGO")

app = FastAPI(
    title=" OPTiMaDe API",
    description=(
        "The [Open Databases Integration for Materials Design (OPTiMaDe) consortium]"
        "(http://http://www.optimade.org/) aims to make materials databases interoperational"
        " by developing a common REST API."
    ),
    version="0.9",
)


def find_data_file(filename):
    import sys, os

    try:
        datadir = os.path.dirname(__file__)
    except:
        datadir = os.path.dirname(sys.executable)
    return os.path.normpath(os.path.join(datadir, filename))


def insertDbValues(db, dbValues: dict):
    """Insert an in memory dump of a db (dbValues) into the given database (db).
A dump consists of either:
    { "<table_name>": [ {<entry1>}, {<entry2>},... ], ...}
or
    { "<table_name>": { <docId1>: {<entry1>}, <docId2>: {<entry2>},... }, ...}
<docId> if given is *not* preserved.
The reason to accept the second format is that it is the default format DBs are stored by tinydb, when
creating db=TinyDB('<someFilePath>'), but we always want to merge entries effectively ignoring the doc_id.
"""
    for tableName, values in dbValues.items():
        table = db.table(tableName)
        if isinstance(values, dict):
            table.insert_multiple(values.values())
        else:
            table.insert_multiple(values)


def loadScratchDB(filePath: str):
    """Loads a db from a json file consisting of
    { "<table_name>": [ {<entry1>}, {<entry2>},... ], ...}
or
    { "<table_name>": { <docId1>: {<entry1>}, <docId2>: {<entry2>},... }, ...}
To an in memory database, and returns that database."""
    db = TinyDB(storage=MemoryStorage)
    with open(filePath) as f:
        dbValues = json.load(f)
    insertDbValues(db, dbValues)
    return db


db_path = Path(find_data_file("tests/optimade_examples.json"))

mainDB = loadScratchDB(db_path)


def convertQuery(query: EntryListingQueryParams):
    """converts a query to a tinydb query to jsonapi formatted objects

    TODO
    """
    from tinydb import Query

    return None


def meta_values(url, data_returned, more_data_available=False):
    """Helper to initialize the meta values"""
    parse_result = urllib.parse.urlparse(url)
    return ResponseMeta(
        query=ResponseMetaQuery(
            representation=f"{parse_result.path}?{parse_result.query}"
        ),
        api_version="v0.9",
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
    )


def update_schema(app):
    """Update OpenAPI schema in file 'local_openapi.json'"""
    with open("local_openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=2)


@app.get(
    "/structures",
    response_model=Union[StructureResponseMany, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Structure"],
)
def get_structures(request: Request, params: EntryListingQueryParams = Depends()):
    structs = mainDB.table("structures")
    q = convertQuery(params)
    if q:
        results = structs.search(q)
    else:
        results = structs.all()
    results = [StructureResource(**x) for x in results]
    more_data_available = False
    # results, more_data_available, data_available = structures.find(params)
    parse_result = urllib.parse.urlparse(str(request.url))
    if more_data_available:
        query = urllib.parse.parse_qs(parse_result.query)
        query["page[offset]"] = int(query.get("page[offset]", "[0]")[0]) + len(results)
        urlencoded = urllib.parse.urlencode(query, doseq=True)
        links = Links(
            next=Link(
                href=f"{parse_result.scheme}://{parse_result.netloc}{parse_result.path}?{urlencoded}"
            )
        )
    else:
        links = Links(next=None)
    res = StructureResponseMany(
        # links=links,
        data=results,
        meta=meta_values(str(request.url), len(results), more_data_available),
    )
    return res


@app.get(
    "/structures/info",
    response_model=Union[EntryInfoResponse, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Structure", "Info"],
)
def get_structures_info(request: Request):
    return EntryInfoResponse(
        meta=meta_values(str(request.url), 1, more_data_available=False),
        data=EntryInfoResource(
            id="",
            type="structures/info",
            attributes=EntryInfoAttributes(
                description="attributes that can be queried",
                properties={
                    "exmpl_p": EntryPropertyInfo(description="a sample custom property")
                },
                output_fields_by_format={
                    "jsonapi": [
                        "id",
                        "type",
                        "elements",
                        "nelements",
                        "chemical_formula",
                        "formula_prototype",
                        "exmpl_p",
                    ]
                },
            ),
        ),
    )


@app.get(
    "/structures/{id}",
    response_model=Union[StructureResponseOne, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Structure"],
)
def get_structures_id(request: Request, id: str):
    results = mainDB.table("structures").search(where("id") == id)
    parse_result = urllib.parse.urlparse(str(request.url))
    if results:
        if len(results) > 1:
            logging.warn("Non unique id {id}".format(id=id))
        data = StructureResource(**results[0])
        return StructureResponseOne(
            data=data, meta=meta_values(str(request.url), 1, more_data_available=False)
        )
    else:
        return StructureResponseOne(
            links=links,
            data=None,
            meta=meta_values(str(request.url), len(results), more_data_available=False),
        )


@app.get(
    "/info",
    response_model=Union[InfoResponse, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Info"],
)
def get_info(request: Request):
    return InfoResponse(
        meta=meta_values(str(request.url), 1, more_data_available=False),
        data=BaseInfoResource(
            attributes=BaseInfoAttributes(
                api_version="v0.9",
                available_api_versions={"v0.9": "http://localhost:5000/"},
                entry_types_by_format={"jsonapi": ["structures"]},
            )
        ),
    )


@app.on_event("startup")
async def startup_event():
    update_schema(app)
