import urllib
from datetime import datetime
from typing import Union, List, Dict

from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from optimade.models import (
    ResponseMeta,
    EntryResource,
    EntryResponseMany,
    EntryResponseOne,
    ToplevelLinks,
    ReferenceResource,
    StructureResource,
)

from optimade.server.config import CONFIG
from optimade.server.deps import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.entry_collections import EntryCollection


ENTRY_INFO_SCHEMAS = {
    "structures": StructureResource.schema,
    "references": ReferenceResource.schema,
}


def meta_values(
    url: str,
    data_returned: int,
    data_available: int,
    more_data_available: bool,
    **kwargs,
) -> ResponseMeta:
    """Helper to initialize the meta values"""
    from optimade import __api_version__
    from optimade.models import ResponseMetaQuery, Provider, Implementation

    parse_result = urllib.parse.urlparse(url)
    provider = CONFIG.provider.copy()
    provider["prefix"] = provider["prefix"][1:-1]  # Remove surrounding `_`
    return ResponseMeta(
        query=ResponseMetaQuery(
            representation=f"{parse_result.path}?{parse_result.query}"
        ),
        api_version=f"v{__api_version__}",
        time_stamp=datetime.utcnow(),
        data_returned=data_returned,
        more_data_available=more_data_available,
        provider=Provider(**provider),
        data_available=data_available,
        implementation=Implementation(**CONFIG.implementation),
        **kwargs,
    )


def handle_response_fields(
    results: Union[List[EntryResource], EntryResource], fields: set
) -> dict:
    if not isinstance(results, list):
        results = [results]
    non_attribute_fields = {"id", "type"}
    top_level = {_ for _ in non_attribute_fields if _ in fields}
    attribute_level = fields - non_attribute_fields
    new_results = []
    while results:
        entry = results.pop(0)
        new_entry = entry.dict(exclude=top_level, exclude_unset=True)
        for field in attribute_level:
            if field in new_entry["attributes"]:
                del new_entry["attributes"][field]
        if not new_entry["attributes"]:
            del new_entry["attributes"]
        new_results.append(new_entry)
    return new_results


def get_included_relationships(
    results: Union[EntryResource, List[EntryResource]],
    ENTRY_COLLECTIONS: Dict[str, EntryCollection],
) -> Dict[str, List[EntryResource]]:
    """Filters the included relationships and makes the appropriate compound request
    to include them in the response.

    Parameters:
        results: list of returned documents.
        ENTRY_COLLECTIONS: dictionary containing collections to query, with key
            based on endpoint type.

    Returns:
        Dictionary with the same keys as ENTRY_COLLECTIONS, each containing the list
            of resource objects for that entry type.

    """
    from collections import defaultdict

    if not isinstance(results, list):
        results = [results]

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
            entry_relationship = relationships.get(entry_type, {})
            if entry_relationship is not None:
                refs = entry_relationship.get("data", [])
                for ref in refs:
                    # could check here and raise a warning if any IDs clash
                    endpoint_includes[entry_type][ref["id"]] = ref

    included = {}
    for entry_type in endpoint_includes:
        compound_filter = " OR ".join(
            ["id={}".format(ref_id) for ref_id in endpoint_includes[entry_type]]
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


def get_base_url(parsed_url_request: urllib.parse.ParseResult) -> str:
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

    included = get_included_relationships(results, ENTRY_COLLECTIONS)

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

    included = get_included_relationships(results, ENTRY_COLLECTIONS)

    if more_data_available:
        raise StarletteHTTPException(
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
            elif value.get("description", "") == "Not allowed key":
                # Special case used in models to make sure not-allowed fields are not present under "attributes"
                # NOTE: This may be removed when upgrading to pydantic v1 !
                continue
            else:
                properties[name] = {"description": value.get("description", "")}
                if "unit" in value:
                    properties[name]["unit"] = value["unit"]
    return properties


def get_providers():
    """Retrieve Materials-Consortia providers (from https://www.optimade.org/providers/links)"""
    import requests
    from bson.objectid import ObjectId

    mat_consortia_providers = requests.get(
        "https://www.optimade.org/providers/links"
    ).json()

    providers_list = []
    for provider in mat_consortia_providers.get("data", []):
        # Remove/skip "exmpl"
        if provider["id"] == "exmpl":
            continue

        provider.update(provider.pop("attributes"))

        # Create MongoDB id
        oid = provider["id"] + provider["type"]
        if len(oid) < 12:
            oid = oid + "0" * (12 - len(oid))
        elif len(oid) > 12:
            oid = oid[:12]
        oid = oid.encode("UTF-8")
        provider["_id"] = {"$oid": ObjectId(oid)}

        providers_list.append(provider)

    return providers_list
