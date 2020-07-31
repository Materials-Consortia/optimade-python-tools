# pylint: disable=import-outside-toplevel,too-many-locals
import re
import urllib
from datetime import datetime
from typing import Union, List, Dict

from fastapi import HTTPException, Request
from starlette.datastructures import URL as StarletteURL

from optimade import __api_version__
from optimade.models import (
    ResponseMeta,
    EntryResource,
    EntryResponseMany,
    EntryResponseOne,
    ToplevelLinks,
    ReferenceResource,
    StructureResource,
    DataType,
)

from optimade.server.config import CONFIG
from optimade.server.entry_collections import EntryCollection
from optimade.server.exceptions import BadRequest
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams

ENTRY_INFO_SCHEMAS = {
    "structures": StructureResource.schema,
    "references": ReferenceResource.schema,
}

# we need to get rid of any release tags (e.g. -rc.2) and any build metadata (e.g. +py36)
# from the api_version before allowing the URL
BASE_URL_PREFIXES = {
    "major": f"/v{__api_version__.split('-')[0].split('+')[0].split('.')[0]}",
    "minor": f"/v{'.'.join(__api_version__.split('-')[0].split('+')[0].split('.')[:2])}",
    "patch": f"/v{'.'.join(__api_version__.split('-')[0].split('+')[0].split('.')[:3])}",
}


def meta_values(
    url: str,
    data_returned: int,
    data_available: int,
    more_data_available: bool,
    **kwargs,
) -> ResponseMeta:
    """Helper to initialize the meta values"""
    from optimade.models import ResponseMetaQuery

    parse_result = urllib.parse.urlparse(url)

    # To catch all (valid) variations of the version part of the URL, a regex is used
    if re.match(r"/v[0-9]+(\.[0-9]+){,2}/.*", parse_result.path) is not None:
        url_path = re.sub(r"/v[0-9]+(\.[0-9]+){,2}/", "/", parse_result.path)
    else:
        url_path = parse_result.path

    return ResponseMeta(
        query=ResponseMetaQuery(representation=f"{url_path}?{parse_result.query}"),
        api_version=__api_version__,
        time_stamp=datetime.now(),
        data_returned=data_returned,
        more_data_available=more_data_available,
        provider=CONFIG.provider,
        data_available=data_available,
        implementation=CONFIG.implementation,
        **kwargs,
    )


def handle_response_fields(
    results: Union[List[EntryResource], EntryResource], exclude_fields: set
) -> dict:
    """Handle query parameter ``response_fields``

    It is assumed that all fields are under ``attributes``.
    This is due to all other top-level fields are REQUIRED in the response.

    :param exclude_fields: Fields under ``attributes`` to be excluded from the response.
    """
    if not isinstance(results, list):
        results = [results]

    new_results = []
    while results:
        entry = results.pop(0)
        new_entry = entry.dict(exclude_unset=True)
        for field in exclude_fields:
            if field in new_entry["attributes"]:
                del new_entry["attributes"][field]
        new_results.append(new_entry)
    return new_results


def get_included_relationships(
    results: Union[EntryResource, List[EntryResource]],
    ENTRY_COLLECTIONS: Dict[str, EntryCollection],
    include_param: List[str],
) -> Dict[str, List[EntryResource]]:
    """Filters the included relationships and makes the appropriate compound request
    to include them in the response.

    Parameters:
        results: list of returned documents.
        ENTRY_COLLECTIONS: dictionary containing collections to query, with key
            based on endpoint type.
        include_param: list of queried related resources that should be included in
            `included`.

    Returns:
        Dictionary with the same keys as ENTRY_COLLECTIONS, each containing the list
            of resource objects for that entry type.

    """
    from collections import defaultdict

    if not isinstance(results, list):
        results = [results]

    for entry_type in include_param:
        if entry_type not in ENTRY_COLLECTIONS and entry_type != "":
            raise BadRequest(
                detail=f"'{entry_type}' cannot be identified as a valid relationship type. "
                f"Known relationship types: {sorted(ENTRY_COLLECTIONS.keys())}"
            )

    endpoint_includes = defaultdict(dict)
    for doc in results:
        # convert list of references into dict by ID to only included unique IDs
        if doc is None:
            continue

        relationships = doc.relationships
        if relationships is None:
            continue

        relationships = relationships.dict()
        for entry_type in ENTRY_COLLECTIONS:
            # Skip entry type if it is not in `include_param`
            if entry_type not in include_param:
                continue

            entry_relationship = relationships.get(entry_type, {})
            if entry_relationship is not None:
                refs = entry_relationship.get("data", [])
                for ref in refs:
                    if ref["id"] not in endpoint_includes[entry_type]:
                        endpoint_includes[entry_type][ref["id"]] = ref

    included = {}
    for entry_type in endpoint_includes:
        compound_filter = " OR ".join(
            ['id="{}"'.format(ref_id) for ref_id in endpoint_includes[entry_type]]
        )
        params = EntryListingQueryParams(
            filter=compound_filter,
            response_format="json",
            response_fields=None,
            sort=None,
            page_limit=0,
            page_offset=0,
        )

        # still need to handle pagination
        ref_results, _, _, _ = ENTRY_COLLECTIONS[entry_type].find(params)
        included[entry_type] = ref_results

    # flatten dict by endpoint to list
    return [obj for endp in included.values() for obj in endp]


def get_base_url(
    parsed_url_request: Union[
        urllib.parse.ParseResult, urllib.parse.SplitResult, StarletteURL
    ]
) -> str:
    """Get base URL for current server

    Take the base URL from the config file, if it exists, otherwise use the request.
    """
    return (
        CONFIG.base_url
        if CONFIG.base_url
        else f"{parsed_url_request.scheme}://{parsed_url_request.netloc}"
    )


def get_entries(
    collection: EntryCollection,
    response: EntryResponseMany,
    request: Request,
    params: EntryListingQueryParams,
) -> EntryResponseMany:
    """Generalized /{entry} endpoint getter"""
    from optimade.server.routers import ENTRY_COLLECTIONS

    results, data_returned, more_data_available, fields = collection.find(params)

    include = []
    if getattr(params, "include", False):
        include.extend(params.include.split(","))
    included = get_included_relationships(results, ENTRY_COLLECTIONS, include)

    if more_data_available:
        # Deduce the `next` link from the current request
        parse_result = urllib.parse.urlparse(str(request.url))
        query = urllib.parse.parse_qs(parse_result.query)
        query["page_offset"] = int(query.get("page_offset", [0])[0]) + len(results)
        urlencoded = urllib.parse.urlencode(query, doseq=True)
        base_url = get_base_url(parse_result)

        links = ToplevelLinks(next=f"{base_url}{parse_result.path}?{urlencoded}")
    else:
        links = ToplevelLinks(next=None)

    if fields:
        results = handle_response_fields(results, fields)

    return response(
        links=links,
        data=results,
        meta=meta_values(
            url=str(request.url),
            data_returned=data_returned,
            data_available=len(collection),
            more_data_available=more_data_available,
        ),
        included=included,
    )


def get_single_entry(
    collection: EntryCollection,
    entry_id: str,
    response: EntryResponseOne,
    request: Request,
    params: SingleEntryQueryParams,
) -> EntryResponseOne:
    from optimade.server.routers import ENTRY_COLLECTIONS

    params.filter = f'id="{entry_id}"'
    results, data_returned, more_data_available, fields = collection.find(params)

    include = []
    if getattr(params, "include", False):
        include.extend(params.include.split(","))
    included = get_included_relationships(results, ENTRY_COLLECTIONS, include)

    if more_data_available:
        raise HTTPException(
            status_code=500,
            detail=f"more_data_available MUST be False for single entry response, however it is {more_data_available}",
        )

    links = ToplevelLinks(next=None)

    if fields and results is not None:
        results = handle_response_fields(results, fields)[0]

    return response(
        links=links,
        data=results,
        meta=meta_values(
            url=str(request.url),
            data_returned=data_returned,
            data_available=len(collection),
            more_data_available=more_data_available,
        ),
        included=included,
    )


def retrieve_queryable_properties(schema: dict, queryable_properties: list) -> dict:
    properties = {}
    for name, value in schema["properties"].items():
        if name in queryable_properties:
            if "$ref" in value:
                path = value["$ref"].split("/")[1:]
                sub_schema = schema.copy()
                while path:
                    next_key = path.pop(0)
                    sub_schema = sub_schema[next_key]
                sub_queryable_properties = sub_schema["properties"].keys()
                properties.update(
                    retrieve_queryable_properties(sub_schema, sub_queryable_properties)
                )
            else:
                properties[name] = {"description": value.get("description", "")}
                if "unit" in value:
                    properties[name]["unit"] = value["unit"]
                # All properties are sortable with the MongoDB backend.
                # While the result for sorting lists may not be as expected, they are still sorted.
                properties[name]["sortable"] = True
                # Try to get OpenAPI-specific "format" if possible, else get "type"; a mandatory OpenAPI key.
                properties[name]["type"] = DataType.from_json_type(
                    value.get("format", value["type"])
                )
    return properties


def mongo_id_for_database(database_id: str, database_type: str) -> str:
    """Produce a MondoDB ObjectId for a database"""
    from bson.objectid import ObjectId

    oid = f"{database_id}{database_type}"
    if len(oid) > 12:
        oid = oid[:12]
    elif len(oid) < 12:
        oid = f"{oid}{'0' * (12 - len(oid))}"

    return str(ObjectId(oid.encode("UTF-8")))


def get_providers():
    """Retrieve Materials-Consortia providers (from https://providers.optimade.org/v1/links)"""
    import requests

    try:
        from optimade.server.data import providers
    except ImportError:
        providers = None

    if providers is None:
        try:
            import simplejson as json
        except ImportError:
            import json

        try:
            providers = requests.get("https://providers.optimade.org/v1/links").json()
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout,
            json.JSONDecodeError,
        ):
            raise BadRequest(
                status_code=500,
                detail="Could not retrieve providers list from https://providers.optimade.org",
            )

    providers_list = []
    for provider in providers.get("data", []):
        # Remove/skip "exmpl"
        if provider["id"] == "exmpl":
            continue

        provider.update(provider.pop("attributes"))

        # Add MongoDB ObjectId
        provider["_id"] = {
            "$oid": mongo_id_for_database(provider["id"], provider["type"])
        }

        providers_list.append(provider)

    return providers_list
