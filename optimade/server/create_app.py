import json
import os
import warnings
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

with warnings.catch_warnings(record=True) as w:
    from optimade.server.config import DEFAULT_CONFIG_FILE_PATH, ServerConfig

    config_warnings = w

from optimade import __api_version__, __version__
from optimade.server.entry_collections import EntryCollection, create_entry_collections
from optimade.server.exception_handlers import OPTIMADE_EXCEPTIONS
from optimade.server.logger import LOGGER
from optimade.server.mappers.entries import BaseResourceMapper
from optimade.server.middleware import OPTIMADE_MIDDLEWARE
from optimade.server.routers import (
    index_info,
    info,
    landing,
    links,
    references,
    structures,
    versions,
)
from optimade.server.routers.utils import BASE_URL_PREFIXES, JSONAPIResponse

MAIN_ENDPOINTS = [info, links, references, structures, landing]
INDEX_ENDPOINTS = [index_info, links]


def add_major_version_base_url(app: FastAPI, index: bool = False):
    """Add mandatory vMajor endpoints, i.e. all except /versions."""
    for endpoint in INDEX_ENDPOINTS if index else MAIN_ENDPOINTS:
        app.include_router(
            endpoint.router, prefix=BASE_URL_PREFIXES["major"], include_in_schema=False
        )


def add_optional_versioned_base_urls(app: FastAPI, index: bool = False):
    """Add the following OPTIONAL prefixes/base URLs to server:
    ```
        /vMajor.Minor
        /vMajor.Minor.Patch
    ```
    """
    for version in ("minor", "patch"):
        for endpoint in INDEX_ENDPOINTS if index else MAIN_ENDPOINTS:
            app.include_router(
                endpoint.router,
                prefix=BASE_URL_PREFIXES[version],
                include_in_schema=False,
            )


def insert_main_data(
    config: ServerConfig, entry_collections: dict[str, EntryCollection]
):
    from optimade.utils import insert_from_jsonl

    for coll_type in ["links", "structures", "references"]:
        if len(entry_collections[coll_type]) > 0:
            LOGGER.info("Skipping data insert: data already present.")
            return

    def _insert_test_data(endpoint: str | None = None):
        import bson.json_util
        from bson.objectid import ObjectId

        import optimade.server.data as data
        from optimade.server.routers.utils import get_providers

        def load_entries(endpoint_name: str, endpoint_collection: EntryCollection):
            LOGGER.debug("Loading test %s...", endpoint_name)

            endpoint_collection.insert(getattr(data, endpoint_name, []))
            if (
                config.database_backend.value in ("mongomock", "mongodb")
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

        if endpoint:
            load_entries(endpoint, entry_collections[endpoint])
        else:
            for name, collection in entry_collections.items():
                load_entries(name, collection)

    if config.insert_from_jsonl:
        jsonl_path = Path(config.insert_from_jsonl)
        LOGGER.debug("Inserting data from JSONL file: %s", jsonl_path)
        if not jsonl_path.exists():
            raise RuntimeError(
                f"Requested JSONL file does not exist: {jsonl_path}. Please specify an absolute group."
            )

        insert_from_jsonl(
            jsonl_path,
            entry_collections,
            create_default_index=config.create_default_index,
        )

        LOGGER.debug("Inserted data from JSONL file: %s", jsonl_path)
        if config.insert_test_data:
            _insert_test_data("links")
    elif config.insert_test_data:
        _insert_test_data()

    if config.exit_after_insert:
        LOGGER.info("Exiting after inserting test data.")
        import sys

        sys.exit(0)


def insert_index_data(
    config: ServerConfig, entry_collections: dict[str, EntryCollection]
):
    import bson.json_util
    from bson.objectid import ObjectId

    from optimade.server.routers.utils import get_providers, mongo_id_for_database

    links_coll = entry_collections["links"]

    if len(links_coll) > 0:
        LOGGER.info("Skipping index links insert: links collection already populated.")
        return

    LOGGER.debug("Loading index links...")
    with open(config.index_links_path) as f:
        data = json.load(f)

    processed = []
    for db in data:
        db["_id"] = {"$oid": mongo_id_for_database(db["id"], db["type"])}
        processed.append(db)

    LOGGER.debug(
        "Inserting index links into collection from %s...", config.index_links_path
    )

    links_coll.insert(bson.json_util.loads(bson.json_util.dumps(processed)))

    if config.database_backend.value in ("mongodb", "mongomock"):
        LOGGER.debug(
            "Adding Materials-Consortia providers to links from optimade.org..."
        )
        providers = get_providers(add_mongo_id=True)
        for doc in providers:
            links_coll.collection.replace_one(  # type: ignore[attr-defined]
                filter={"_id": ObjectId(doc["_id"]["$oid"])},
                replacement=bson.json_util.loads(bson.json_util.dumps(doc)),
                upsert=True,
            )

        LOGGER.debug("Done inserting index links!")

    else:
        LOGGER.warning(
            "Not inserting test data for index meta-database for backend %s",
            config.database_backend.value,
        )


def create_app(config: ServerConfig | None = None, index: bool = False) -> FastAPI:
    if config_warnings:
        LOGGER.warning(
            f"Invalid config file or no config file provided, running server with default settings. Errors: "
            f"{[warnings.formatwarning(w.message, w.category, w.filename, w.lineno, '') for w in config_warnings]}"
        )
    else:
        LOGGER.info(
            f"Loaded settings from {os.getenv('OPTIMADE_CONFIG_FILE', DEFAULT_CONFIG_FILE_PATH)}."
        )

    if config is None:
        config = ServerConfig()

    if config.debug:  # pragma: no cover
        LOGGER.info("DEBUG MODE")

    title = "OPTIMADE API" if not index else "OPTIMADE API - Index meta-database"
    description = """The [Open Databases Integration for Materials Design (OPTIMADE) consortium](https://www.optimade.org/) aims to make materials databases interoperational by developing a common REST API.\n"""
    if index:
        description += 'This is the "special" index meta-database.\n'
    description += f"\nThis specification is generated using [`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools/tree/v{__version__}) v{__version__}."

    if index:
        config.is_index = True

    app = FastAPI(
        root_path=config.root_path,
        title=title,
        description=description,
        version=__api_version__,
        docs_url=f"{BASE_URL_PREFIXES['major']}/extensions/docs",
        redoc_url=f"{BASE_URL_PREFIXES['major']}/extensions/redoc",
        openapi_url=f"{BASE_URL_PREFIXES['major']}/extensions/openapi.json",
        default_response_class=JSONAPIResponse,
        separate_input_output_schemas=False,
    )

    # Save the config in the app state for access in endpoints
    app.state.config = config

    # create entry collections and save in app state for access in endpoints
    entry_collections = create_entry_collections(config)
    app.state.entry_collections = entry_collections

    # store also the BaseResourceMapper
    app.state.base_resource_mapper = BaseResourceMapper()

    if not index:
        if config.insert_test_data or config.insert_from_jsonl:
            insert_main_data(config, entry_collections)
    else:
        if config.insert_test_data and config.index_links_path.exists():
            insert_index_data(config, entry_collections)

    # Add CORS middleware first
    app.add_middleware(CORSMiddleware, allow_origins=["*"])

    # Then add required OPTIMADE middleware
    for middleware in OPTIMADE_MIDDLEWARE:
        app.add_middleware(middleware)

    # Enable GZIP after other middleware.
    if config.gzip.enabled:
        app.add_middleware(
            GZipMiddleware,
            minimum_size=config.gzip.minimum_size,
            compresslevel=config.gzip.compresslevel,
        )

    # Add exception handlers
    for exception, handler in OPTIMADE_EXCEPTIONS:
        app.add_exception_handler(exception, handler)

    # Add various endpoints to unversioned URL
    endpoints = INDEX_ENDPOINTS if index else MAIN_ENDPOINTS
    endpoints += [versions]
    for endpoint in endpoints:
        app.include_router(endpoint.router)

    # add the versioned endpoints
    add_major_version_base_url(app, index=index)
    add_optional_versioned_base_urls(app, index=index)

    return app
