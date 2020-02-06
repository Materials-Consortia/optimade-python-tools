# pylint: disable=line-too-long
import json
import os
from pathlib import Path

from lark.exceptions import VisitError

from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .entry_collections import MongoCollection
from .config import CONFIG
from .middleware import RedirectSlashedURLs
from .routers import info, links, references, structures
from .routers.utils import get_providers, BASE_URL_PREFIXES

from optimade import __api_version__, __version__
import optimade.server.exception_handlers as exc_handlers


app = FastAPI(
    title="OPTiMaDe API",
    description=(
        f"""The [Open Databases Integration for Materials Design (OPTiMaDe) consortium](https://www.optimade.org/) aims to make materials databases interoperational by developing a common REST API.

This specification is generated using [`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools/tree/v{__version__}) v{__version__}."""
    ),
    version=__api_version__,
    docs_url=f"{BASE_URL_PREFIXES['regular']['major']}/extensions/docs",
    redoc_url=f"{BASE_URL_PREFIXES['regular']['major']}/extensions/redoc",
    openapi_url=f"{BASE_URL_PREFIXES['regular']['major']}/extensions/openapi.json",
)


test_paths = {
    "structures": Path(__file__).resolve().parent.joinpath("data/test_structures.json"),
    "references": Path(__file__).resolve().parent.joinpath("data/test_references.json"),
    "links": Path(__file__).resolve().parent.joinpath("data/test_links.json"),
}
if not CONFIG.use_real_mongo and all(path.exists() for path in test_paths.values()):
    import bson.json_util
    from .routers import ENTRY_COLLECTIONS

    def load_entries(endpoint_name: str, endpoint_collection: MongoCollection):
        print(f"loading test {endpoint_name}...")
        with open(test_paths[endpoint_name]) as f:
            data = json.load(f)
            print(f"inserting test {endpoint_name} into collection...")
            endpoint_collection.collection.insert_many(
                bson.json_util.loads(bson.json_util.dumps(data))
            )
        if endpoint_name == "links":
            print("adding Materials-Consortia providers to links from optimade.org")
            endpoint_collection.collection.insert_many(
                bson.json_util.loads(bson.json_util.dumps(get_providers()))
            )
        print(f"done inserting test {endpoint_name}...")

    for name, collection in ENTRY_COLLECTIONS.items():
        load_entries(name, collection)


# Add various middleware
app.add_middleware(RedirectSlashedURLs)


# Add various exception handlers
app.add_exception_handler(StarletteHTTPException, exc_handlers.http_exception_handler)
app.add_exception_handler(
    RequestValidationError, exc_handlers.request_validation_exception_handler
)
app.add_exception_handler(ValidationError, exc_handlers.validation_exception_handler)
app.add_exception_handler(VisitError, exc_handlers.grammar_not_implemented_handler)
app.add_exception_handler(Exception, exc_handlers.general_exception_handler)


# Add various endpoints to `/optimade/vMAJOR`
app.include_router(info.router, prefix=BASE_URL_PREFIXES["regular"]["major"])
app.include_router(links.router, prefix=BASE_URL_PREFIXES["regular"]["major"])
app.include_router(references.router, prefix=BASE_URL_PREFIXES["regular"]["major"])
app.include_router(structures.router, prefix=BASE_URL_PREFIXES["regular"]["major"])


def add_optional_versioned_base_urls(app: FastAPI):
    """Add the following OPTIONAL prefixes/base URLs to server:
    ```
        /optimade/vMajor.Minor
        /optimade/vMajor.Minor.Patch
    ```
    """
    for version in ("minor", "patch"):
        app.include_router(info.router, prefix=BASE_URL_PREFIXES["regular"][version])
        app.include_router(links.router, prefix=BASE_URL_PREFIXES["regular"][version])
        app.include_router(
            references.router, prefix=BASE_URL_PREFIXES["regular"][version]
        )
        app.include_router(
            structures.router, prefix=BASE_URL_PREFIXES["regular"][version]
        )


def update_schema(app: FastAPI):
    """Update OpenAPI schema in file 'local_openapi.json'"""
    package_root = Path(__file__).parent.parent.parent.resolve()
    if not package_root.joinpath("openapi").exists():
        os.mkdir(package_root.joinpath("openapi"))
    with open(package_root.joinpath("openapi/local_openapi.json"), "w") as f:
        json.dump(app.openapi(), f, indent=2)


@app.on_event("startup")
async def startup_event():
    # Update OpenAPI schema on versioned base URL `/optimade/vMAJOR`
    update_schema(app)
    # Add API endpoints for OPTIONAL base URLs `/optimade/vMAJOR.MINOR` and `/optimade/vMAJOR.MINOR.PATCH`
    add_optional_versioned_base_urls(app)
