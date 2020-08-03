"""The OPTIMADE server

The server is based on MongoDB, using either `pymongo` or `mongomock`.

This is an example implementation with example data.
To implement your own server see the documentation at https://optimade.org/optimade-python-tools.
"""

import warnings

from lark.exceptions import VisitError

from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

with warnings.catch_warnings(record=True) as w:
    from optimade.server.config import CONFIG

    config_warnings = w

from optimade import __api_version__, __version__
import optimade.server.exception_handlers as exc_handlers
from optimade.server.entry_collections import MongoCollection
from optimade.server.logger import LOGGER
from optimade.server.middleware import (
    AddWarnings,
    CheckWronglyVersionedBaseUrls,
    EnsureQueryParamIntegrity,
    HandleApiHint,
)
from optimade.server.routers import (
    info,
    landing,
    links,
    references,
    structures,
    versions,
)
from optimade.server.routers.utils import get_providers, BASE_URL_PREFIXES


if CONFIG.config_file is None:
    LOGGER.warn(
        f"Invalid config file or no config file provided, running server with default settings. Errors: "
        f"{[warnings.formatwarning(w.message, w.category, w.filename, w.lineno, '') for w in config_warnings]}"
    )
else:
    LOGGER.info(f"Loaded settings from {CONFIG.config_file}.")

if CONFIG.debug:  # pragma: no cover
    LOGGER.info("DEBUG MODE")

app = FastAPI(
    title="OPTIMADE API",
    description=(
        f"""The [Open Databases Integration for Materials Design (OPTIMADE) consortium](https://www.optimade.org/) aims to make materials databases interoperational by developing a common REST API.

This specification is generated using [`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools/tree/v{__version__}) v{__version__}."""
    ),
    version=__api_version__,
    docs_url=f"{BASE_URL_PREFIXES['major']}/extensions/docs",
    redoc_url=f"{BASE_URL_PREFIXES['major']}/extensions/redoc",
    openapi_url=f"{BASE_URL_PREFIXES['major']}/extensions/openapi.json",
)


if not CONFIG.use_real_mongo:
    import bson.json_util
    import optimade.server.data as data
    from .routers import ENTRY_COLLECTIONS

    def load_entries(endpoint_name: str, endpoint_collection: MongoCollection):
        LOGGER.debug(f"Loading test {endpoint_name}...")

        endpoint_collection.collection.insert_many(getattr(data, endpoint_name, []))
        if endpoint_name == "links":
            LOGGER.debug(
                "Adding Materials-Consortia providers to links from optimade.org"
            )
            endpoint_collection.collection.insert_many(
                bson.json_util.loads(bson.json_util.dumps(get_providers()))
            )
        LOGGER.debug(f"Done inserting test {endpoint_name}...")

    for name, collection in ENTRY_COLLECTIONS.items():
        load_entries(name, collection)


# Add various middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_middleware(EnsureQueryParamIntegrity)
app.add_middleware(CheckWronglyVersionedBaseUrls)
app.add_middleware(HandleApiHint)
app.add_middleware(AddWarnings)


# Add various exception handlers
app.add_exception_handler(StarletteHTTPException, exc_handlers.http_exception_handler)
app.add_exception_handler(
    RequestValidationError, exc_handlers.request_validation_exception_handler
)
app.add_exception_handler(ValidationError, exc_handlers.validation_exception_handler)
app.add_exception_handler(VisitError, exc_handlers.grammar_not_implemented_handler)
app.add_exception_handler(NotImplementedError, exc_handlers.not_implemented_handler)
app.add_exception_handler(Exception, exc_handlers.general_exception_handler)

# Add various endpoints to unversioned URL
for endpoint in (info, links, references, structures, landing, versions):
    app.include_router(endpoint.router)


def add_major_version_base_url(app: FastAPI):
    """ Add mandatory vMajor endpoints, i.e. all except versions. """
    for endpoint in (info, links, references, structures, landing):
        app.include_router(endpoint.router, prefix=BASE_URL_PREFIXES["major"])


def add_optional_versioned_base_urls(app: FastAPI):
    """Add the following OPTIONAL prefixes/base URLs to server:
    ```
        /vMajor.Minor
        /vMajor.Minor.Patch
    ```
    """
    for version in ("minor", "patch"):
        for endpoint in (info, links, references, structures, landing):
            app.include_router(endpoint.router, prefix=BASE_URL_PREFIXES[version])


@app.on_event("startup")
async def startup_event():
    # Add API endpoints for MANDATORY base URL `/vMAJOR`
    add_major_version_base_url(app)
    # Add API endpoints for OPTIONAL base URLs `/vMAJOR.MINOR` and `/vMAJOR.MINOR.PATCH`
    add_optional_versioned_base_urls(app)
