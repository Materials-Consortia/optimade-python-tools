"""The OPTIMADE server

The server is based on MongoDB, using either `pymongo` or `mongomock`.

This is an example implementation with example data.
To implement your own server see the documentation at https://optimade.org/optimade-python-tools.
"""
import os
import warnings

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

with warnings.catch_warnings(record=True) as w:
    from optimade.server.config import CONFIG, DEFAULT_CONFIG_FILE_PATH

    config_warnings = w

from optimade import __api_version__, __version__
from optimade.server.entry_collections import EntryCollection
from optimade.server.exception_handlers import OPTIMADE_EXCEPTIONS
from optimade.server.logger import LOGGER
from optimade.server.middleware import OPTIMADE_MIDDLEWARE
from optimade.server.routers import (
    info,
    landing,
    links,
    partial_data,
    references,
    structures,
    versions,
)
from optimade.server.routers.utils import BASE_URL_PREFIXES, JSONAPIResponse

if config_warnings:
    LOGGER.warn(
        f"Invalid config file or no config file provided, running server with default settings. Errors: "
        f"{[warnings.formatwarning(w.message, w.category, w.filename, w.lineno, '') for w in config_warnings]}"
    )
else:
    LOGGER.info(
        f"Loaded settings from {os.getenv('OPTIMADE_CONFIG_FILE', DEFAULT_CONFIG_FILE_PATH)}."
    )

if CONFIG.debug:  # pragma: no cover
    LOGGER.info("DEBUG MODE")

app = FastAPI(
    root_path=CONFIG.root_path,
    title="OPTIMADE API",
    description=(
        f"""The [Open Databases Integration for Materials Design (OPTIMADE) consortium](https://www.optimade.org/) aims to make materials databases interoperational by developing a common REST API.

This specification is generated using [`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools/tree/v{__version__}) v{__version__}."""
    ),
    version=__api_version__,
    docs_url=f"{BASE_URL_PREFIXES['major']}/extensions/docs",
    redoc_url=f"{BASE_URL_PREFIXES['major']}/extensions/redoc",
    openapi_url=f"{BASE_URL_PREFIXES['major']}/extensions/openapi.json",
    default_response_class=JSONAPIResponse,
)


if CONFIG.insert_test_data:
    import bson.json_util
    from bson.objectid import ObjectId

    import optimade.server.data as data
    from optimade.server.routers import ENTRY_COLLECTIONS
    from optimade.server.routers.utils import get_providers

    # Todo Do we need to check a file is not already stored in gridfs?
    # Load test data from files into gridfs

    if CONFIG.database_backend.value in ("mongomock", "mongodb"):
        from pathlib import Path

        import numpy

        from optimade.server.routers.partial_data import partial_data_coll

        # todo create seperate function for storing data files in gridfs
        # read_array_header function originally from https://stackoverflow.com/a/64226659 by https://stackoverflow.com/users/982257/iguananaut
        def read_array_header(fobj):
            version = numpy.lib.format.read_magic(fobj)
            func_name = "read_array_header_" + "_".join(str(v) for v in version)
            func = getattr(numpy.lib.format, func_name)
            return func(fobj)

        for filename, filetype, metadata in getattr(data, "data_files", []):
            with open(Path(__file__).parent / "data" / filename, "rb") as f:
                if filetype == "numpy":
                    numpy_meta = read_array_header(f)
                    if "slice_obj" not in metadata:
                        slice_obj = [
                            {"start": 1, "stop": i, "step": 1} for i in numpy_meta[0]
                        ]
                        metadata["sliceobj"] = slice_obj
                    if "dtype" not in metadata:
                        metadata["dtype"] = {
                            "name": numpy_meta[2].name,
                            "itemsize": numpy_meta[2].itemsize,
                        }
                partial_data_coll.insert([{"data": f, "filename": filename, "metadata": metadata}])  # type: ignore[list-item] # Todo : Perhaps this can be reduced to a single insert statement.

    def load_entries(endpoint_name: str, endpoint_collection: EntryCollection):
        LOGGER.debug("Loading test %s...", endpoint_name)

        endpoint_collection.insert(getattr(data, endpoint_name, []))
        if (
            CONFIG.database_backend.value in ("mongomock", "mongodb")
            and endpoint_name == "links"
        ):
            LOGGER.debug(
                "Adding Materials-Consortia providers to links from optimade.org"
            )
            providers = get_providers(add_mongo_id=True)
            for doc in providers:
                endpoint_collection.collection.replace_one(  # type: ignore[attr-defined]
                    filter={"_id": ObjectId(doc["_id"]["$oid"])},
                    replacement=bson.json_util.loads(bson.json_util.dumps(doc)),
                    upsert=True,
                )
        LOGGER.debug("Done inserting test %s!", endpoint_name)

    for name, collection in ENTRY_COLLECTIONS.items():
        load_entries(name, collection)

# Add CORS middleware first
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Then add required OPTIMADE middleware
for middleware in OPTIMADE_MIDDLEWARE:
    app.add_middleware(middleware)

# Add exception handlers
for exception, handler in OPTIMADE_EXCEPTIONS:
    app.add_exception_handler(exception, handler)

# Add various endpoints to unversioned URL
for endpoint in (info, links, references, structures, landing, versions, partial_data):
    app.include_router(endpoint.router)


def add_major_version_base_url(app: FastAPI):
    """Add mandatory vMajor endpoints, i.e. all except versions."""
    for endpoint in (info, links, references, structures, landing, partial_data):
        app.include_router(endpoint.router, prefix=BASE_URL_PREFIXES["major"])


def add_optional_versioned_base_urls(app: FastAPI):
    """Add the following OPTIONAL prefixes/base URLs to server:
    ```
        /vMajor.Minor
        /vMajor.Minor.Patch
    ```
    """
    for version in ("minor", "patch"):
        for endpoint in (info, links, references, structures, landing, partial_data):
            app.include_router(endpoint.router, prefix=BASE_URL_PREFIXES[version])


@app.on_event("startup")
async def startup_event():
    # Add API endpoints for MANDATORY base URL `/vMAJOR`
    add_major_version_base_url(app)
    # Add API endpoints for OPTIONAL base URLs `/vMAJOR.MINOR` and `/vMAJOR.MINOR.PATCH`
    add_optional_versioned_base_urls(app)
