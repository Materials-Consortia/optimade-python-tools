# pylint: disable=import-outside-toplevel,too-many-locals
import re
import sys
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Set, Union
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.datastructures import URL as StarletteURL
from bson.objectid import ObjectId

from optimade import __api_version__
from optimade.models import (
    ResponseMeta,
    EntryResource,
    EntryResponseMany,
    EntryResponseOne,
    ToplevelLinks,
)

from optimade.server.config import CONFIG, SupportedResponseFormats
from optimade.server.entry_collections import EntryCollection
from optimade.server.exceptions import BadRequest, InternalServerError
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.utils import mongo_id_for_database, get_providers, PROVIDER_LIST_URLS
from optimade.adapters.hdf5 import generate_hdf5_file_content

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

FORMAT_SIZE_FACTORS = {"hdf5": 1.0, "json": 4.7}


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
    schema: str,
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
        schema=schema,
        **kwargs,
    )


def handle_response_fields(
    results: Union[List[EntryResource], EntryResource],
    exclude_fields: Set[str],
    include_fields: Set[str],
    params: Union[EntryListingQueryParams, SingleEntryQueryParams],
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
    single_entry = False
    if not isinstance(results, list):
        single_entry = True
        results = [results]
    sum_entry_size = 0
    continue_from_frame = getattr(params, "continue_from_frame", None)
    new_results = []
    traj_trunc = False
    last_frame = None
    # TODO the code below only needs to be executed if there is a trajectory endpoint
    if params.response_format in [_.value for _ in CONFIG.max_response_size]:
        data_limit = CONFIG.max_response_size[
            SupportedResponseFormats(params.response_format)
        ]
    elif "json" in [_.value for _ in CONFIG.max_response_size]:
        data_limit = CONFIG.max_response_size[SupportedResponseFormats("json")]
    else:
        data_limit = 10
    # When the data is encoded in the json format the numerical data may take up more space to take this into account we use a format dependend conversion factor.
    data_limit = int(data_limit * 1000000 / FORMAT_SIZE_FACTORS[params.response_format])

    while results:
        one_doc = results.pop(0)
        if one_doc:
            new_entry = one_doc.dict(exclude_unset=True, by_alias=True)
        else:
            new_results = [[]]
            break
        # TODO This function has become very large. It would be good to split it up.
        # TODO For now we only have trajectories with large properties but it would be nice if this could apply to other endpoints in the future as well.
        if new_entry["type"] == "trajectories":
            last_frame = getattr(params, "last_frame", None)
            # Originaly we started counting the frames from 0, now we count from one so we subtract 1 from first_frame and later also from last frame, so the old code can be used
            first_frame = getattr(params, "first_frame") - 1
            if (
                last_frame is None or last_frame > new_entry["attributes"]["nframes"]
            ):  # In principple it is possible to retrieve multiple trajectories while the value of last_frame is set . Not all of these may have llast_frame frames. so we choose to lower the va;lue of last frame instead of throwing an error.
                last_frame = new_entry["attributes"]["nframes"] - 1
            else:
                last_frame = last_frame - 1

            frame_step = getattr(params, "frame_step")
            if continue_from_frame:
                first_frame = continue_from_frame
                continue_from_frame = None

            if frame_step is None:
                # frame_step_set = False
                frame_step = 1
            # else:
            # frame_step_set = True

            # We make a rough estimate of the amount of data expected.
            sum_item_size = 0
            # Todo add number of atoms*12 for sum_item_size and decide whether we want to split up response in small pieces.

            for field_name in include_fields:
                if field_name in new_entry["attributes"]["available_properties"].keys():
                    if new_entry["attributes"]["available_properties"][field_name][
                        "frame_serialization_format"
                    ] in [
                        "explicit",
                        "explicit_custom_sparse",
                        "explicit_regular_sparse",
                    ]:
                        if field_name in new_entry["attributes"]["reference_structure"]:
                            item_size = sys.getsizeof(
                                new_entry["attributes"]["reference_structure"][
                                    field_name
                                ]
                            )
                        else:
                            item_size = (
                                12
                                * new_entry["attributes"]["reference_structure"][
                                    "nsites"
                                ]
                            )  # make a conservative guess of the size of the item. # TODO add a field to the database entry specifying the average size of the item per frame.
                        sum_item_size += item_size
            data_size = sum_item_size * ((last_frame - first_frame + 1) // frame_step)
            if (sum_entry_size + data_size) > data_limit:
                data_left = data_limit - sum_entry_size
                n_frames_to_read = max(
                    data_left // sum_item_size, 1
                )  # TODO take into account whether other trajectories have been returned previously if so this value may also be 0
                traj_trunc = True
                last_frame = first_frame + frame_step * (n_frames_to_read - 1)
            sum_entry_size += sum_item_size * (
                (last_frame - first_frame + 1) // frame_step
            )

            #
            # # Case data has been read from MongDB In that case we may need to reduce the data ranges accoording to first_frame , last_frame and frame_step
            # # Retrieve field from file if not stored in database # TODO It would be nice if it would not just say file but also give the file type.
            #
            #     path = getattr(one_doc.attributes, "_storage_path", None)
            #     if path is None:
            #         raise InternalServerError(
            #             f"The property{field} is supposed to be stored in a file yet no filepath is specified in _storage_path."
            #         )
            for field in include_fields:
                if field == "cartesian_site_positions":
                    field = "cartesian_site_positions"
                    new_entry["attributes"][field] = {}
                    new_entry["attributes"][field]["first_frame"] = (
                        first_frame + 1
                    )  # because OPTIMADE indexes from 1 we have to add 1 here
                    new_entry["attributes"][field]["frame_step"] = frame_step
                    new_entry["attributes"][field]["last_frame"] = last_frame + 1

                    new_entry["attributes"][field][
                        "frame_serialization_format"
                    ] = "explicit"
                    values = get_values_from_file(
                        field, "trajectory.bin", new_entry, "bioxl"
                    )
                    new_entry["attributes"][field]["values"] = values
                    new_entry["attributes"][field]["nvalues"] = len(values)
                elif field in new_entry["attributes"]["available_properties"]:
                    new_entry["attributes"][field] = {}
                    new_entry["attributes"][field][
                        "frame_serialization_format"
                    ] = "constant"
                    new_entry["attributes"][field]["values"] = new_entry["attributes"][
                        "reference_structure"
                    ][field]
                    new_entry["attributes"][field]["nvalues"] = 1

        # Add missing fields
        for field in include_fields:
            if field not in new_entry["attributes"]:
                new_entry["attributes"][field] = None

        # Remove fields excluded by their omission in `response_fields`
        for field in exclude_fields:
            if field in new_entry["attributes"]:
                del new_entry["attributes"][field]

        new_results.append(new_entry)
        if traj_trunc:
            break
    if single_entry:
        return new_results[0], traj_trunc, last_frame
    else:
        return new_results, traj_trunc, last_frame


def get_values_from_file(field: str, path: str, new_entry: Dict, storage_method: str):

    if (
        new_entry["attributes"]["available_properties"][field][
            "frame_serialization_format"
        ]
        != "explicit"
    ):
        raise InternalServerError(
            "Loading data from a file is not implemented yet for frame serialization methods other than 'explicit'."
        )  # TODO implement this for the other frame_serialization_methods
    first_frame = new_entry["attributes"][field]["first_frame"] - 1
    last_frame = new_entry["attributes"][field]["last_frame"]
    frame_step = new_entry["attributes"][field]["frame_step"]
    nsites = new_entry["attributes"]["reference_structure"]["nsites"]
    # TODO Add support for a varying number of sites per frame.
    if storage_method == "hdf5":
        return get_hdf5_value(field, path, first_frame, last_frame, frame_step)
    elif field == "cartesian_site_positions":
        if storage_method == "bioxl":
            return get_from_binary_gridfs(
                new_entry["attributes"]["_id"],
                path,
                first_frame,
                last_frame,
                frame_step,
                nsites,
            )
        elif storage_method == "binary":
            values = get_binary_value(path, first_frame, last_frame, frame_step, nsites)
            return values
    else:
        raise InternalServerError(
            f"Unable to retrieve data for the field {field} with _storage_method field:{storage_method}"
        )


def get_hdf5_value(
    field: str, path: str, first_frame: int, last_frame: int, frame_step: int
):
    import h5py

    file = h5py.File(path, "r")
    return file[field]["values"][first_frame:last_frame:frame_step]


def get_binary_value(
    path: str, first_frame: int, last_frame: int, frame_step: int, nsites: int
):
    import numpy

    with open(path, "r") as binary_file:

        nframes_to_return = (last_frame - first_frame + 1) // frame_step
        if frame_step == 1:
            values = numpy.fromfile(
                binary_file,
                dtype="<f",
                count=(last_frame - first_frame + 1) * nsites * 3,
                sep="",
                offset=(first_frame) * nsites * 3 * 4,
            )
        else:
            values = numpy.array([])
            for i in range(nframes_to_return):
                values = numpy.concatenate(
                    [
                        values,
                        numpy.fromfile(
                            binary_file,
                            dtype="<f",
                            count=nsites * 3,
                            sep="",
                            offset=(first_frame + i * frame_step) * nsites * 3 * 4,
                        ),
                    ]
                )
    return values.reshape((nframes_to_return, nsites, 3))


def get_from_binary_gridfs(
    id: Union[ObjectId, str],
    filename: str,
    first_frame: int,
    last_frame: int,
    frame_step: int,
    nsites: int,
):
    import gridfs
    import numpy
    from optimade.server.entry_collections.mongo import (
        CLIENT,
    )  # Todo: Once there is a filles endpoint we should be able to use the files collection.

    if isinstance(id, str):
        id = ObjectId(id)
    fs = gridfs.GridFS(CLIENT[CONFIG.mongo_database])
    file = fs.find_one(
        {"filename": filename, "metadata.project": id}
    )  # Todo it may be more efficient to extract the file id from the project instead.
    if file is None:
        raise FileNotFoundError(
            f"The file with {filename} and id: {id} was not found on the gridfs system in the {CONFIG.mongo_database} database."
        )
    # TODO Add support for a varying number of sites per frame.
    frame_size = 12 * nsites
    nframes = int(1 + ((last_frame - (first_frame + 1)) / frame_step))
    if frame_step == 1:
        file.seek(frame_size * first_frame, whence=0)
        binary_data = file.read(frame_size * (last_frame - first_frame))
    else:
        binary_data = b""
        start = first_frame * frame_size
        for i in range(nframes):
            file.seek(start)
            binary_data += file.read(frame_size)
            start += frame_size * frame_step

    return numpy.frombuffer(binary_data, dtype="<f").reshape((nframes, nsites, 3))


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
    included = get_included_relationships(results, ENTRY_COLLECTIONS, include)

    traj_trunc = False
    if fields or include_fields:
        results, traj_trunc, last_frame = handle_response_fields(
            results, fields, include_fields, params
        )

    if traj_trunc:
        more_data_available = True
    if more_data_available:
        # Deduce the `next` link from the current request
        query = urllib.parse.parse_qs(request.url.query)
        query["page_offset"] = int(query.get("page_offset", [0])[0]) + len(results)
        if traj_trunc:
            query["page_offset"] -= 1
            query["continue_from_frame"] = last_frame + 2
        urlencoded = urllib.parse.urlencode(query, doseq=True)
        base_url = get_base_url(request.url)

        links = ToplevelLinks(next=f"{base_url}{request.url.path}?{urlencoded}")
    else:
        links = ToplevelLinks(next=None)

    response_object = response(
        links=links,
        data=results,
        meta=meta_values(
            url=request.url,
            data_returned=data_returned,
            data_available=len(collection),
            more_data_available=more_data_available,
            schema=CONFIG.schema_url,
        ),
        included=included,
    )

    if params.response_format in CONFIG.get_enabled_response_formats():
        if params.response_format == "json":
            return response_object
        elif params.response_format == "hdf5":
            return Response(
                content=generate_hdf5_file_content(response_object),
                media_type="application/x-hdf5",
                headers={
                    "Content-disposition": f"attachment; filename={collection.collection.name}.hdf5"
                },
            )
    else:
        raise BadRequest(
            detail=f"The response_format {params.response_format} is not supported by this server. Use one of the supported formats: {','.join(CONFIG.get_enabled_response_formats())} instead "
        )


def get_single_entry(
    collection: EntryCollection,
    entry_id: str,
    response: EntryResponseOne,
    request: Request,
    params: SingleEntryQueryParams,
) -> EntryResponseOne:
    from optimade.server.routers import ENTRY_COLLECTIONS

    params.check_params(request.query_params)
    pattern = re.compile("^[0-9a-f]{24}$")
    if pattern.match(entry_id):
        params.filter = f'id="{entry_id}" OR _id="{entry_id}"'
    else:
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

    traj_trunc = False
    if fields or include_fields and results is not None:
        results, traj_trunc, last_frame = handle_response_fields(
            results, fields, include_fields, params
        )
        # results = handle_response_fields(results, fields, include_fields, params)[0]

    if traj_trunc:
        more_data_available = True
        # Deduce the `next` link from the current request
        query = urllib.parse.parse_qs(request.url.query)
        query["page_offset"] = int(query.get("page_offset", [0])[0]) + len(results) - 1
        query["continue_from_frame"] = last_frame + 2
        urlencoded = urllib.parse.urlencode(query, doseq=True)
        base_url = get_base_url(request.url)
        links = ToplevelLinks(next=f"{base_url}{request.url.path}?{urlencoded}")
    else:
        links = ToplevelLinks(next=None)

    response_object = response(
        links=links,
        data=results,
        meta=meta_values(
            url=request.url,
            data_returned=data_returned,
            data_available=len(collection),
            more_data_available=more_data_available,
            schema=CONFIG.schema_url,
        ),
        included=included,
    )
    if params.response_format in CONFIG.get_enabled_response_formats():
        if params.response_format == "json":
            return response_object
        elif params.response_format == "hdf5":
            return Response(
                content=generate_hdf5_file_content(response_object),
                media_type="application/x-hdf5",
                headers={
                    "Content-disposition": f"attachment; filename={entry_id}.hdf5"
                },
            )
    else:
        raise BadRequest(
            detail=f"The response_format {params.response_format} is not supported by this server. Use one of the supported formats: {','.join(CONFIG.get_enabled_response_formats())} instead "
        )
