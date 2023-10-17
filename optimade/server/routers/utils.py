# pylint: disable=import-outside-toplevel,too-many-locals
import io
import re
import urllib.parse
from datetime import datetime
from typing import Any, Optional, Union

import numpy as np
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.datastructures import URL as StarletteURL

from optimade import __api_version__
from optimade.adapters.jsonl import to_jsonl
from optimade.exceptions import BadRequest, InternalServerError, NotFound
from optimade.models import (  # type: ignore[attr-defined]
    EntryResource,  # type: ignore[attr-defined]
    EntryResponseMany,
    EntryResponseOne,
    ResponseMeta,  # type: ignore[attr-defined]
    ToplevelLinks,  # type: ignore[attr-defined]
)
from optimade.server.config import CONFIG
from optimade.server.entry_collections import EntryCollection
from optimade.server.query_params import (
    EntryListingQueryParams,
    PartialDataQueryParams,
    SingleEntryQueryParams,
)
from optimade.utils import PROVIDER_LIST_URLS, get_providers, mongo_id_for_database

__all__ = (
    "BASE_URL_PREFIXES",
    "meta_values",
    "handle_response_fields",
    "get_included_relationships",
    "get_base_url",
    "get_entries",
    "get_single_entry",
    "mongo_id_for_database",
    "get_providers",
    "PROVIDER_LIST_URLS",
)

# we need to get rid of any release tags (e.g. -rc.2) and any build metadata (e.g. +py36)
# from the api_version before allowing the URL
BASE_URL_PREFIXES = {
    "major": f"/v{__api_version__.split('-')[0].split('+')[0].split('.')[0]}",
    "minor": f"/v{'.'.join(__api_version__.split('-')[0].split('+')[0].split('.')[:2])}",
    "patch": f"/v{'.'.join(__api_version__.split('-')[0].split('+')[0].split('.')[:3])}",
}


class JSONAPIResponse(JSONResponse):
    """This class simply patches `fastapi.responses.JSONResponse` to use the
    JSON:API 'application/vnd.api+json' MIME type.

    """

    media_type = "application/vnd.api+json"


def meta_values(
    url: Union[urllib.parse.ParseResult, urllib.parse.SplitResult, StarletteURL, str],
    data_returned: Optional[int],
    data_available: int,
    more_data_available: bool,
    schema: Optional[str] = None,
    **kwargs,
) -> ResponseMeta:
    """Helper to initialize the meta values"""
    from optimade.models import ResponseMetaQuery  # type: ignore[attr-defined]

    if isinstance(url, str):
        url = urllib.parse.urlparse(url)

    # To catch all (valid) variations of the version part of the URL, a regex is used
    if re.match(r"/v[0-9]+(\.[0-9]+){,2}/.*", url.path) is not None:
        url_path = re.sub(r"/v[0-9]+(\.[0-9]+){,2}/", "/", url.path)
    else:
        url_path = url.path

    if schema is None:
        schema = CONFIG.schema_url if not CONFIG.is_index else CONFIG.index_schema_url

    return ResponseMeta(
        query=ResponseMetaQuery(representation=f"{url_path}?{url.query}"),
        api_version=__api_version__,
        time_stamp=datetime.now(),
        data_returned=data_returned,
        more_data_available=more_data_available,
        provider=CONFIG.provider,
        data_available=data_available,
        implementation=CONFIG.implementation,
        schema=schema,
        **kwargs,
    )


def handle_response_fields(
    results: Union[list[EntryResource], EntryResource, list[dict], dict],
    exclude_fields: set[str],
    include_fields: set[str],
) -> list[dict[str, Any]]:
    """Handle query parameter `response_fields`.

    It is assumed that all fields are under `attributes`.
    This is due to all other top-level fields are REQUIRED in the response.

    Parameters:
        exclude_fields: Fields under `attributes` to be excluded from the response.
        include_fields: Fields under `attributes` that were requested that should be
            set to null if missing in the entry.

    Returns:
        List of resulting resources as dictionaries after pruning according to
        the `response_fields` OPTIMADE URL query parameter.

    """
    if not isinstance(results, list):
        results = [results]

    new_results = []
    while results:
        new_entry = results.pop(0)
        try:
            new_entry = new_entry.dict(exclude_unset=True, by_alias=True)  # type: ignore[union-attr]
        except AttributeError:
            pass

        # Remove fields excluded by their omission in `response_fields`
        for field in exclude_fields:
            if field in new_entry["attributes"]:
                del new_entry["attributes"][field]
            if new_entry.get("meta") and (
                property_meta_data_fields := new_entry.get("meta").get(  # type: ignore[union-attr]
                    "property_metadata"
                )
            ):
                if field in property_meta_data_fields:
                    del new_entry["meta"]["property_metadata"][field]

        # Include missing fields that were requested in `response_fields`
        for field in include_fields:
            if field not in new_entry["attributes"]:
                new_entry["attributes"][field] = None

        new_results.append(new_entry)

    return new_results


def get_included_relationships(
    results: Union[EntryResource, list[EntryResource], dict, list[dict]],
    ENTRY_COLLECTIONS: dict[str, EntryCollection],
    include_param: list[str],
) -> list[Union[EntryResource, dict]]:
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

    endpoint_includes: dict[Any, dict] = defaultdict(dict)
    for doc in results:
        # convert list of references into dict by ID to only included unique IDs
        if doc is None:
            continue

        try:
            relationships = doc.relationships  # type: ignore
        except AttributeError:
            relationships = doc.get("relationships", None)

        if relationships is None:
            continue

        if not isinstance(relationships, dict):
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

    included: dict[
        str, Union[list[EntryResource], EntryResource, list[dict], dict]
    ] = {}
    for entry_type in endpoint_includes:
        compound_filter = " OR ".join(
            [f'id="{ref_id}"' for ref_id in endpoint_includes[entry_type]]
        )
        params = EntryListingQueryParams(
            filter=compound_filter,
            response_format="json",
            response_fields="",
            sort="",
            page_limit=0,
            page_offset=0,
        )

        # still need to handle pagination
        ref_results, _, _, _, _ = ENTRY_COLLECTIONS[entry_type].find(params)
        if ref_results is None:
            ref_results = []
        included[entry_type] = ref_results

    # flatten dict by endpoint to list
    return [obj for endp in included.values() for obj in endp]


def get_base_url(
    parsed_url_request: Union[
        urllib.parse.ParseResult, urllib.parse.SplitResult, StarletteURL, str
    ]
) -> str:
    """Get base URL for current server

    Take the base URL from the config file, if it exists, otherwise use the request.
    """
    parsed_url_request = (
        urllib.parse.urlparse(parsed_url_request)
        if isinstance(parsed_url_request, str)
        else parsed_url_request
    )
    return (
        CONFIG.base_url.rstrip("/")
        if CONFIG.base_url
        else f"{parsed_url_request.scheme}://{parsed_url_request.netloc}"
    )


def generate_links_partial_data(
    results,
    parsed_url_request: Union[
        urllib.parse.ParseResult, urllib.parse.SplitResult, StarletteURL, str
    ],
):
    for entry in results:
        if entry.get("meta", {}) and entry["meta"].get("partial_data_links", {}):
            for property in entry["meta"]["partial_data_links"]:
                for response_format in CONFIG.partial_data_formats:
                    entry["meta"]["partial_data_links"][property].append(
                        {
                            "format": str(response_format.value),
                            "link": get_base_url(parsed_url_request)
                            + "/partial_data/"
                            + entry["id"]
                            + "?response_fields="
                            + property
                            + "&response_format="
                            + str(response_format.value),
                        }
                    )


def get_entries(
    collection: EntryCollection,
    response: type[EntryResponseMany],  # noqa
    request: Request,
    params: EntryListingQueryParams,
) -> dict:
    """Generalized /{entry} endpoint getter"""
    from optimade.server.routers import ENTRY_COLLECTIONS

    params.check_params(request.query_params)
    (
        results,
        data_returned,
        more_data_available,
        fields,
        include_fields,
    ) = collection.find(params)

    include = []
    if getattr(params, "include", False):
        include.extend(params.include.split(","))

    included = []
    if results is not None:
        generate_links_partial_data(results, request.url)
        included = get_included_relationships(results, ENTRY_COLLECTIONS, include)

    if more_data_available:
        # Deduce the `next` link from the current request
        query = urllib.parse.parse_qs(request.url.query)
        query.update(collection.get_next_query_params(params, results))

        urlencoded = urllib.parse.urlencode(query, doseq=True)
        base_url = get_base_url(request.url)

        links = ToplevelLinks(next=f"{base_url}{request.url.path}?{urlencoded}")
    else:
        links = ToplevelLinks(next=None)

    if results is not None and (fields or include_fields):
        results = handle_response_fields(results, fields, include_fields)  # type: ignore[assignment]

    return dict(
        links=links,
        data=results if results else [],
        meta=meta_values(
            url=request.url,
            data_returned=data_returned,
            data_available=len(collection),
            more_data_available=more_data_available,
            schema=CONFIG.schema_url
            if not CONFIG.is_index
            else CONFIG.index_schema_url,
        ),
        included=included,
    )


def get_single_entry(
    collection: EntryCollection,
    entry_id: str,
    response: type[EntryResponseOne],
    request: Request,
    params: SingleEntryQueryParams,
) -> dict:
    from optimade.server.routers import ENTRY_COLLECTIONS

    params.check_params(request.query_params)
    params.filter = f'id="{entry_id}"'  # type: ignore[attr-defined]
    (
        results,
        data_returned,
        more_data_available,
        fields,
        include_fields,
    ) = collection.find(params)

    if more_data_available:
        raise InternalServerError(
            detail=f"more_data_available MUST be False for single entry response, however it is {more_data_available}",
        )

    include = []
    if getattr(params, "include", False):
        include.extend(params.include.split(","))

    included = []
    if results is not None:
        included = get_included_relationships(results, ENTRY_COLLECTIONS, include)
        generate_links_partial_data([results], request.url)

    links = ToplevelLinks(next=None)

    if results is not None and (fields or include_fields):
        results = handle_response_fields(results, fields, include_fields)[0]  # type: ignore[assignment]

    return dict(
        links=links,
        data=results if results else None,
        meta=meta_values(
            url=request.url,
            data_returned=data_returned,
            data_available=len(collection),
            more_data_available=more_data_available,
            schema=CONFIG.schema_url
            if not CONFIG.is_index
            else CONFIG.index_schema_url,
        ),
        included=included,
    )


def get_partial_entry(
    collection: EntryCollection,
    entry_id: str,
    request: Request,
    params: Union[PartialDataQueryParams],
) -> dict:
    # from optimade.server.routers import ENTRY_COLLECTIONS

    params.check_params(request.query_params)
    params.filter = f'parent_id="{entry_id}"'
    (
        results,
        data_returned,
        more_data_available,
        fields,
        include_fields,
    ) = collection.find(params)

    links = ToplevelLinks(next=None)

    if results is None:
        raise NotFound(
            detail=f"No data available for the combination of entry {entry_id} and property {params.response_fields}",
        )

    array = np.frombuffer(
        results["attributes"]["data"],  # type: ignore[call-overload]
        dtype=getattr(np, results["attributes"]["dtype"]["name"]),  # type: ignore[call-overload]
    ).reshape(
        results["attributes"]["shape"]  # type: ignore[call-overload]
    )
    # slice array
    property_ranges = results["attributes"]["property_ranges"]  # type: ignore[call-overload]
    slice_ind = [
        slice(
            0,
            1 + property_ranges[0]["stop"] - property_ranges[0]["start"],
            property_ranges[0]["step"],
        )
    ]
    for dim_range in property_ranges[1:]:
        slice_ind.append(
            slice(dim_range["start"] - 1, dim_range["stop"], dim_range["step"])
        )
    array = array[tuple(slice_ind)]

    if fields or include_fields:
        results = handle_response_fields(results, fields, include_fields)[0]  # type: ignore[assignment]

    # todo make the implementation of these formats more universal. i.e. allow them for other endpoint as well,

    sliceobj = []
    for i in array.shape:
        sliceobj.append({"start": 1, "stop": i, "step": 1})
    header = {
        "optimade-partial-data": {"format": "1.2.0"},
        "layout": "dense",
        "property_name": params.response_fields,
        "returned_ranges": sliceobj,
        # "entry": {"id": entry_id, "type": None}, #Todo add type information to metadata entry
        "has_references": False,
    }  # Todo: add support for non_dense data
    if more_data_available:
        next_link = ["PARTIAL-DATA-NEXT", [results["attributes"].pop("next")]]  # type: ignore[call-overload]

    if params.response_format == "json":
        for key in header:
            results["attributes"][key] = header[key]  # type: ignore[call-overload]
        results["attributes"]["data"] = array.tolist()  # type: ignore[call-overload]
        if more_data_available:
            results["attributes"]["next"] = next_link  # type: ignore[call-overload]
        return dict(
            links=links,
            data=[results] if results else None,
            meta=meta_values(
                url=request.url,
                data_returned=data_returned,
                data_available=len(collection),
                more_data_available=more_data_available,
                schema=CONFIG.schema_url
                if not CONFIG.is_index
                else CONFIG.index_schema_url,
            ),
            # included=included,
        )

    jsonl_content = [header, array.tolist()]
    if more_data_available:
        jsonl_content.append(next_link)
    return Response(
        content=to_jsonl(jsonl_content),
        media_type="application/jsonlines",
        headers={
            "Content-disposition": f"attachment; filename={entry_id + ':' + params.response_fields}.jsonl"
        },
    )


def convert_data_to_str(results):
    values = results["attributes"]["data"]
    if isinstance(values, bytes):
        results["attributes"]["data"] = np.array2string(np.load(io.BytesIO(values)))
    return results
