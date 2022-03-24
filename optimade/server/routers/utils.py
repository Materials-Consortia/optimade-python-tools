# pylint: disable=import-outside-toplevel,too-many-locals
import re
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Set, Union

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.datastructures import URL as StarletteURL

from optimade import __api_version__
from optimade.models import (
    ResponseMeta,
    EntryResource,
    EntryResponseMany,
    EntryResponseOne,
    ToplevelLinks,
)

from optimade.server.config import CONFIG
from optimade.server.entry_collections import EntryCollection
from optimade.server.exceptions import BadRequest, InternalServerError
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.utils import mongo_id_for_database, get_providers, PROVIDER_LIST_URLS

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
    data_returned: int,
    data_available: int,
    more_data_available: bool,
    **kwargs,
) -> ResponseMeta:
    """Helper to initialize the meta values"""
    from optimade.models import ResponseMetaQuery

    if isinstance(url, str):
        url = urllib.parse.urlparse(url)

    # To catch all (valid) variations of the version part of the URL, a regex is used
    if re.match(r"/v[0-9]+(\.[0-9]+){,2}/.*", url.path) is not None:
        url_path = re.sub(r"/v[0-9]+(\.[0-9]+){,2}/", "/", url.path)
    else:
        url_path = url.path

    return ResponseMeta(
        query=ResponseMetaQuery(representation=f"{url_path}?{url.query}"),
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
    results: Union[List[EntryResource], EntryResource],
    exclude_fields: Set[str],
    include_fields: Set[str],
    params: EntryListingQueryParams,
) -> List[Dict[str, Any]]:
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
        one_doc = results.pop(0)
        new_entry = one_doc.dict(exclude_unset=True, by_alias=True)

        # Include missing fields that were requested in `response_fields`
        for field in include_fields:
            if field not in new_entry["attributes"]:
                new_entry["attributes"][field] = None
            else:  # apply slicing to the trajectory
                storage_method = getattr(
                    getattr(one_doc.attributes, field), "_storage_location", None
                )
                if storage_method is not None:
                    frame_serialization_format = new_entry["attributes"][field][
                        "frame_serialization_format"
                    ]
                    last_frame = getattr(params, "last_frame")
                    first_frame = getattr(params, "first_frame")
                    frame_step = getattr(params, "frame_step")
                    if last_frame is None:
                        last_frame = (
                            new_entry["attributes"]["nframes"] - 1
                        )  # The frames are counted starting from 0 so if nframes = 10 the last frame is frame 9.
                    # handle last_frame first_frame an frame step for the different ways in which the data could be encoded.

                    new_entry["attributes"][field]["first_frame"] = first_frame
                    new_entry["attributes"][field]["frame_step"] = frame_step
                    new_entry["attributes"][field]["last_frame"] = last_frame

                    if (
                        storage_method == "file"
                    ):  # Retrieve field from file if not stored in database
                        # Case file stored in file # TODO It would be nice if it would not just say file but also give the file type.
                        path = getattr(
                            one_doc.attributes, "_hdf5file_path", None
                        )  # TODO perhaps hdf5file is not such a good name and we should be more generic like datalocation
                        if path is None:
                            raise InternalServerError(
                                f"The property{field} is supposed to be stored in a file yet no filepath is specified in hdf5file_path."
                            )
                        values = get_values_from_file(
                            field, path, params, frame_serialization_format
                        )
                    elif (
                        storage_method == "mongo"
                    ):  # Case data has been read from MongDB In that case we may need to reduce the data ranges
                        values = []
                        if (
                            frame_serialization_format == "explicit"
                        ):  # ToDo add warning if the set value of framestep
                            if last_frame:
                                last_frame += 1
                            new_entry["attributes"][field]["values"] = new_entry[
                                "attributes"
                            ][field]["values"][first_frame:last_frame:frame_step]
                        elif frame_serialization_format == "explicit_regular_sparse":
                            step_size_sparse = new_entry["attributes"][field].get(
                                "step_size_sparse"
                            )
                            offset = new_entry["attributes"][field].get(
                                "offset_sparse", 0
                            )

                            if first_frame - offset % step_size_sparse == 0:
                                if frame_step % step_size_sparse == 0:
                                    values = new_entry["attributes"][field]["values"][
                                        (first_frame - offset)
                                        / step_size_sparse : (
                                            last_frame / step_size_sparse
                                        )
                                        + 1 : frame_step / step_size_sparse
                                    ]
                                else:
                                    for frame in range(
                                        first_frame, last_frame, frame_step
                                    ):
                                        if (frame - offset) % step_size_sparse == 0:
                                            index = int(
                                                (frame - offset) / step_size_sparse
                                            )
                                            values.append(
                                                new_entry["attributes"][field][
                                                    "values"
                                                ][index]
                                            )
                                        else:
                                            values.append(None)

                            elif frame_step % step_size_sparse == 0:
                                values = [None] * (
                                    1 + (last_frame - first_frame) / frame_step
                                )
                            else:
                                for frame in range(first_frame, last_frame, frame_step):
                                    if (frame - offset) % step_size_sparse == 0:
                                        index = int((frame - offset) / step_size_sparse)
                                        values.append(
                                            new_entry["attributes"][field]["values"][
                                                index
                                            ]
                                        )
                                    else:
                                        values.append(None)
                        elif frame_serialization_format == "explicit_custom_sparse":
                            frames = new_entry["attributes"][field]["frames"]
                            index = -1
                            sparse_frame = -1
                            for requested_frame in range(
                                first_frame, last_frame, frame_step
                            ):
                                found = False
                                while sparse_frame <= requested_frame:
                                    if sparse_frame == requested_frame:
                                        found = True
                                        break
                                    index += 1
                                    sparse_frame = frames[index]
                                if found:
                                    values.append(
                                        new_entry["attributes"][field]["values"][index]
                                    )
                                else:
                                    values.append(None)
                            new_entry["attributes"][field]["frames"] = list(
                                range(first_frame, last_frame, frame_step)
                            )
                    else:
                        raise InternalServerError(
                            f"Unknown value for the _storage_location field:{new_entry['attributes'][field]['_storage_location']}"
                        )
                    new_entry["attributes"][field]["values"] = values
                    new_entry["attributes"][field]["nvalues"] = len(values)

        # Remove fields excluded by their omission in `response_fields`
        for field in exclude_fields:
            if field in new_entry["attributes"]:
                del new_entry["attributes"][field]

        new_results.append(new_entry)
    return new_results


def get_values_from_file(
    field: str, path: str, params: EntryListingQueryParams, frame_serialization_method
):
    import h5py

    first_frame = getattr(params, "first_frame")
    last_frame = getattr(params, "last_frame")
    if last_frame:
        last_frame += 1
    frame_step = getattr(params, "frame_step")
    file = h5py.File(path, "r")
    if frame_serialization_method == "explicit":
        return file[field]["values"][first_frame:last_frame:frame_step].tolist()
    else:
        raise InternalServerError(
            "Loading data from is not implemented yet for frame serialization methods other than 'explicit'."
        )


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
        ref_results, _, _, _, _ = ENTRY_COLLECTIONS[entry_type].find(params)
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


def get_entries(
    collection: EntryCollection,
    response: EntryResponseMany,
    request: Request,
    params: EntryListingQueryParams,
) -> EntryResponseMany:
    """Generalized /{entry} endpoint getter"""
    from optimade.server.routers import ENTRY_COLLECTIONS

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
    included = get_included_relationships(results, ENTRY_COLLECTIONS, include)

    if more_data_available:
        # Deduce the `next` link from the current request
        query = urllib.parse.parse_qs(request.url.query)
        query["page_offset"] = int(query.get("page_offset", [0])[0]) + len(results)
        urlencoded = urllib.parse.urlencode(query, doseq=True)
        base_url = get_base_url(request.url)

        links = ToplevelLinks(next=f"{base_url}{request.url.path}?{urlencoded}")
    else:
        links = ToplevelLinks(next=None)

    if fields or include_fields:
        results = handle_response_fields(results, fields, include_fields, params)

    return response(
        links=links,
        data=results,
        meta=meta_values(
            url=request.url,
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
    included = get_included_relationships(results, ENTRY_COLLECTIONS, include)

    if more_data_available:
        raise InternalServerError(
            detail=f"more_data_available MUST be False for single entry response, however it is {more_data_available}",
        )

    links = ToplevelLinks(next=None)

    if fields or include_fields and results is not None:
        results = handle_response_fields(results, fields, include_fields, params)[0]

    return response(
        links=links,
        data=results,
        meta=meta_values(
            url=request.url,
            data_returned=data_returned,
            data_available=len(collection),
            more_data_available=more_data_available,
        ),
        included=included,
    )
