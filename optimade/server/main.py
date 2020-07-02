# pylint: disable=line-too-long

from lark.exceptions import VisitError

from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

from optimade import __api_version__, __version__
import optimade.server.exception_handlers as exc_handlers

from .entry_collections import MongoCollection
from .config import CONFIG
from .middleware import EnsureQueryParamIntegrity
from .routers import info, links, references, structures, landing, versions
from .routers.utils import get_providers, BASE_URL_PREFIXES


if CONFIG.debug:  # pragma: no cover
    print("DEBUG MODE")


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
        print(f"loading test {endpoint_name}...")

        endpoint_collection.collection.insert_many(getattr(data, endpoint_name, []))
        if endpoint_name == "links":
            print("adding Materials-Consortia providers to links from optimade.org")
            endpoint_collection.collection.insert_many(
                bson.json_util.loads(bson.json_util.dumps(get_providers()))
            )
        print(f"done inserting test {endpoint_name}...")

    for name, collection in ENTRY_COLLECTIONS.items():
        load_entries(name, collection)


# Add various middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_middleware(EnsureQueryParamIntegrity)


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
