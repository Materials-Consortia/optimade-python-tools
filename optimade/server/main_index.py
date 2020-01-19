import os
import json
from pathlib import Path

from lark.exceptions import VisitError

from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import CONFIG
from .routers import index_info, links

from optimade import __api_version__
import optimade.server.exception_handlers as exc_handlers


app = FastAPI(
    title="OPTiMaDe API - Index meta-database",
    description=(
        "The [Open Databases Integration for Materials Design (OPTiMaDe) consortium]"
        "(http://http://www.optimade.org/) aims to make materials databases interoperational "
        "by developing a common REST API.\n"
        'This is the "special" index meta-database.'
    ),
    version=__api_version__,
    docs_url="/index/optimade/extensions/docs",
    redoc_url="/index/optimade/extensions/redoc",
    openapi_url="/index/optimade/extensions/openapi.json",
)


if not CONFIG.use_real_mongo and CONFIG.index_links_path.exists():
    import bson.json_util
    from .routers.links import links_coll

    print("loading index links...")
    with open(CONFIG.index_links_path) as f:
        data = json.load(f)
        print("inserting index links into collection...")
        links_coll.collection.insert_many(
            bson.json_util.loads(bson.json_util.dumps(data))
        )
    print("done inserting index links...")


app.add_exception_handler(StarletteHTTPException, exc_handlers.http_exception_handler)
app.add_exception_handler(
    RequestValidationError, exc_handlers.request_validation_exception_handler
)
app.add_exception_handler(ValidationError, exc_handlers.validation_exception_handler)
app.add_exception_handler(VisitError, exc_handlers.grammar_not_implemented_handler)
app.add_exception_handler(Exception, exc_handlers.general_exception_handler)


# Create the following prefixes:
#   /optimade
#   /optimade/vMajor (but only if Major >= 1)
#   /optimade/vMajor.Minor
#   /optimade/vMajor.Minor.Patch
valid_prefixes = ["/index/optimade"]
version = [int(_) for _ in app.version.split(".")]
while version:
    if version[0] or len(version) >= 2:
        valid_prefixes.append(
            "/index/optimade/v{}".format(".".join([str(_) for _ in version]))
        )
    version.pop(-1)

for prefix in valid_prefixes:
    app.include_router(index_info.router, prefix=prefix)
    app.include_router(links.router, prefix=prefix)


def update_schema(app):
    """Update OpenAPI schema in file 'local_index_openapi.json'"""
    package_root = Path(__file__).parent.parent.parent.resolve()
    if not package_root.joinpath("openapi").exists():
        os.mkdir(package_root.joinpath("openapi"))
    with open(package_root.joinpath("openapi/local_index_openapi.json"), "w") as f:
        json.dump(app.openapi(), f, indent=2)


@app.on_event("startup")
async def startup_event():
    update_schema(app)
