from typing import Any, Dict, List, Tuple, Type, Union

from optimade.exceptions import BadRequest
from optimade.filtertransformers.mongo import MongoTransformer
from optimade.models import EntryResource  # type: ignore[attr-defined]
from optimade.server.config import CONFIG, SupportedBackend, SupportedResponseFormats
from optimade.server.entry_collections import EntryCollection
from optimade.server.logger import LOGGER
from optimade.server.mappers import BaseResourceMapper  # type: ignore[attr-defined]
from optimade.server.query_params import (
    EntryListingQueryParams,
    PartialDataQueryParams,
    SingleEntryQueryParams,
)

if CONFIG.database_backend.value == "mongodb":
    from pymongo import MongoClient, version_tuple

    if version_tuple[0] < 4:
        LOGGER.warning(
            "Support for pymongo<=3 (and thus MongoDB v3) is deprecated and will be "
            "removed in the next minor release."
        )

    LOGGER.info("Using: Real MongoDB (pymongo)")

elif CONFIG.database_backend.value == "mongomock":
    import mongomock.gridfs
    from mongomock import MongoClient

    LOGGER.info("Using: Mock MongoDB (mongomock)")
    mongomock.gridfs.enable_gridfs_integration()

if CONFIG.database_backend.value in ("mongomock", "mongodb"):
    CLIENT = MongoClient(CONFIG.mongo_uri)
    import gridfs


class MongoBaseCollection(EntryCollection):
    def _check_aliases(self, aliases):
        """Check that aliases do not clash with mongo keywords."""
        if any(
            alias[0].startswith("$") or alias[1].startswith("$") for alias in aliases
        ):
            raise RuntimeError(f"Cannot define an alias starting with a '$': {aliases}")


class GridFSCollection(MongoBaseCollection):
    """Class for querying gridfs collections (implemented by either pymongo or mongomock)."""

    def __init__(
        self,
        name: str,
        resource_cls: Type[EntryResource],
        resource_mapper: Type[BaseResourceMapper],
        database: str = CONFIG.mongo_database,
    ):
        """Initialize the GridFSCollection for the given parameters.

        Parameters:
            name: The name of the collection.
            resource_cls: The type of entry resource that is stored by the collection.
            resource_mapper: A resource mapper object that handles aliases and
                format changes between deserialization and response.
            database: The name of the underlying MongoDB database to connect to.

        """
        super().__init__(
            resource_cls,
            resource_mapper,
            MongoTransformer(mapper=resource_mapper),
        )
        db = MongoClient(CONFIG.mongo_uri)[
            database
        ]  # Somehow importing the client from optimade.server.entry_collections.mongo gives an error that the type of db is not "Database" even though it is.

        self.collection = gridfs.GridFS(db, name)

        # check aliases do not clash with mongo operators
        self._check_aliases(self.resource_mapper.all_aliases())
        self._check_aliases(self.resource_mapper.all_length_aliases())

    def __len__(self) -> int:
        """Returns the total number of entries in the collection."""
        return len(self.collection.list())

    def count(self, **kwargs: Any) -> int:
        """Returns the number of entries matching the query specified
        by the keyword arguments.

        Parameters:
            **kwargs: Query parameters as keyword arguments. The keys
                'filter', 'skip', 'limit', 'hint' and 'maxTimeMS' will be passed
                to the `pymongo.collection.Collection.count_documents` method.

        """
        for k in list(kwargs.keys()):
            if k not in ("filter", "skip", "limit", "hint", "maxTimeMS"):
                del kwargs[k]
        if "filter" not in kwargs:  # "filter" is needed for count_documents()
            kwargs["filter"] = {}
        return len(self.collection.find(**kwargs))

    def insert(self, content: bytes, filename: str, metadata: dict = {}) -> None:
        """Add the given entries to the underlying database.

        Warning:
            No validation is performed on the incoming data.

        Arguments:
            content: The file content to add to gridfs.
            filename: The filename of the added content.
            metadata: extra metadata to add to the gridfs entry.
        """
        self.collection.put(content, filename=filename, metadata=metadata)

    def handle_query_params(
        self, params: Union[SingleEntryQueryParams, PartialDataQueryParams]
    ) -> Dict[str, Any]:
        """Parse and interpret the backend-agnostic query parameter models into a dictionary
        that can be used by MongoDB.

        This Mongo-specific method calls the base `EntryCollection.handle_query_params` method
        and adds additional handling of the MongoDB ObjectID type.

        Parameters:
            params: The initialized query parameter model from the server.

        Raises:
            Forbidden: If too large of a page limit is provided.
            BadRequest: If an invalid request is made, e.g., with incorrect fields
                or response format.

        Returns:
            A dictionary representation of the query parameters.

        """

        criteria = super().handle_query_params(params)
        # Handle MongoDB ObjectIDs:
        # - If they were not requested, then explicitly remove them
        # - If they were requested, then cast them to strings in the response
        if "_id" not in criteria.get("projection", {}):
            criteria["projection"]["_id"] = False

        if "page_above" in criteria:
            raise NotImplementedError(
                "`page_above` is not implemented for this backend."
            )

        if criteria.get("projection", {}).get("_id"):
            criteria["projection"]["_id"] = {"$toString": "$_id"}

        if isinstance(params, PartialDataQueryParams):
            entry_id = params.filter.split("=")[1][1:-1]
            criteria["filter"] = {
                "filename": {
                    "$eq": f"{entry_id}:{params.response_fields}.npy"
                }  # todo Should we add support for other file extensions?
            }  # Todo make sure response fields has only one value

        # response_format
        if getattr(params, "response_format", False) and params.response_format not in (
            x.value for x in CONFIG.partial_data_formats
        ):
            raise BadRequest(
                detail=f"Response format {params.response_format} is not supported, please use one of the supported response formats: {', '.join((x.value for x in CONFIG.partial_data_formats))}"
            )
        criteria["response_format"] = params.response_format
        criteria["property_ranges"] = params.property_ranges

        return criteria

    # todo test if it is more efficient to use the get method of gridfs
    def _run_db_query(
        self,
        criteria: Dict[str, Any],
        single_entry: bool = False,
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Run the query on the backend and collect the results.

        Arguments:
            criteria: A dictionary representation of the query parameters.
            single_entry: Whether or not the caller is expecting a single entry response.

        Returns:
            The list of entries from the database (without any re-mapping), the total number of
            entries matching the query and a boolean for whether or not there is more data available.

        """

        # TODO handle case where the type does not have a fixed width. For example strings or dictionaries.
        response_format = criteria.pop("response_format")
        max_return_size = (
            CONFIG.max_response_size[SupportedResponseFormats(response_format)]
            * 1024
            * 1024
        )  # todo adjust for different output formats(take into account that the number of numbers to read is larger for a text based output format than for a binary format.
        results = []
        filterdict = criteria.pop("filter", {})

        # I have tried to use just **criteria as is mentioned in the documentation but this does not seem to work.
        gridcursor = self.collection.find(filterdict)
        more_data_available = False
        nresults = 0
        # todo add code that can handle very sparse requests where reading individual sections of files is more efficient.
        for (
            file_obj
        ) in (
            gridcursor
        ):  # Next throws an error when there are zero files returned, so I use a for loop instead to get one result.
            nresults += 1
            metadata = file_obj.metadata
            property_ranges = self.parse_property_ranges(
                criteria.pop("property_ranges", None),
                metadata["slice_obj"],
                metadata["dim_names"],
            )
            item_size = metadata["dtype"]["itemsize"]
            dim_sizes = [
                (i["stop"] - i["start"] + 1) // i["step"] for i in metadata["slice_obj"]
            ]
            top_stepsize = 1
            for i in dim_sizes[1:]:
                top_stepsize *= i
            offset = (property_ranges[0]["start"] - 1) * item_size * top_stepsize
            np_header = file_obj.readline()
            file_obj.seek(
                offset + len(np_header)
            )  # set the correct starting point fo the read from the gridfs file system.
            if (max_return_size / item_size) < (
                1 + property_ranges[0]["stop"] - property_ranges[0]["start"]
            ) * top_stepsize:  # case more data requested then fits in the response
                more_data_available = True
                n_val_return = max_return_size / item_size
                n_outer = max(
                    int(n_val_return / top_stepsize), 1
                )  # always read at least one line for now.
                read_size = n_outer * top_stepsize * item_size
                shape = [n_outer] + dim_sizes[1:]
            else:
                read_size = (
                    (1 + property_ranges[0]["stop"] - property_ranges[0]["start"])
                    * top_stepsize
                    * item_size
                )
                shape = [
                    1 + property_ranges[0]["stop"] - property_ranges[0]["start"]
                ] + dim_sizes[1:]

            values = file_obj.read(read_size)
            entry = {
                "id": metadata.get("parent_id", None),
                "type": metadata.get("endpoint", None),
            }
            results = [
                {
                    "type": "partial_data",
                    "id": str(file_obj._id),
                    "property_name": metadata.get("property_name", None),
                    "entry": entry,
                    "data": values,
                    "dtype": metadata["dtype"],
                    "shape": shape,
                    "property_ranges": property_ranges,
                }
            ]
            if more_data_available:
                property_ranges_str = f"property_ranges={metadata['dim_names'][0]}:{property_ranges[0]['start']+n_outer}:{property_ranges[0]['stop']}:{property_ranges[0]['step']}"
                for i, name in enumerate(metadata["dim_names"][1:]):
                    property_ranges_str += f",{name}:{property_ranges[i+1]['start']}:{property_ranges[i+1]['stop']}:{property_ranges[i+1]['step']}"
                results[0][
                    "next"
                ] = f"{CONFIG.base_url}/partial_data/{metadata['parent_id']}?response_fields={metadata['property_name']}&response_format={response_format}&{property_ranges_str}"
            break

        return results, nresults, more_data_available

    def parse_property_ranges(
        self, property_range_str: str, attribute_slice_obj: list, dim_names: list
    ) -> List[dict]:
        property_range_dict = {}
        if property_range_str:
            ranges = [dimrange.split(":") for dimrange in property_range_str.split(",")]

            for subrange in ranges:
                property_range_dict[subrange[0]] = {
                    "start": int(subrange[1])
                    if subrange[1]
                    else attribute_slice_obj[dim_names.index(subrange[0])]["start"],
                    "stop": int(subrange[2])
                    if subrange[2]
                    else attribute_slice_obj[dim_names.index(subrange[0])]["stop"],
                    "step": int(subrange[3])
                    if subrange[3]
                    else attribute_slice_obj[dim_names.index(subrange[0])]["step"],
                }
        for i, dim in enumerate(dim_names):
            if dim not in property_range_dict:
                property_range_dict[dim] = attribute_slice_obj[i]

        return [property_range_dict[dim] for dim in dim_names]


class MongoCollection(MongoBaseCollection):
    """Class for querying MongoDB collections (implemented by either pymongo or mongomock)
    containing serialized [`EntryResource`][optimade.models.entries.EntryResource]s objects.

    """

    def __init__(
        self,
        name: str,
        resource_cls: Type[EntryResource],
        resource_mapper: Type[BaseResourceMapper],
        database: str = CONFIG.mongo_database,
    ):
        """Initialize the MongoCollection for the given parameters.

        Parameters:
            name: The name of the collection.
            resource_cls: The type of entry resource that is stored by the collection.
            resource_mapper: A resource mapper object that handles aliases and
                format changes between deserialization and response.
            database: The name of the underlying MongoDB database to connect to.

        """
        super().__init__(
            resource_cls,
            resource_mapper,
            MongoTransformer(mapper=resource_mapper),
        )

        self.collection = CLIENT[database][name]

        # check aliases do not clash with mongo operators
        self._check_aliases(self.resource_mapper.all_aliases())
        self._check_aliases(self.resource_mapper.all_length_aliases())

    def __len__(self) -> int:
        """Returns the total number of entries in the collection."""
        return self.collection.estimated_document_count()

    def count(self, **kwargs: Any) -> int:
        """Returns the number of entries matching the query specified
        by the keyword arguments.

        Parameters:
            **kwargs: Query parameters as keyword arguments. The keys
                'filter', 'skip', 'limit', 'hint' and 'maxTimeMS' will be passed
                to the `pymongo.collection.Collection.count_documents` method.

        """
        for k in list(kwargs.keys()):
            if k not in ("filter", "skip", "limit", "hint", "maxTimeMS"):
                del kwargs[k]
        if "filter" not in kwargs:  # "filter" is needed for count_documents()
            kwargs["filter"] = {}
        return self.collection.count_documents(**kwargs)

    def insert(self, data: List[EntryResource]) -> None:
        """Add the given entries to the underlying database.

        Warning:
            No validation is performed on the incoming data.

        Arguments:
            data: The entry resource objects to add to the database.

        """
        self.collection.insert_many(data)

    def handle_query_params(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> Dict[str, Any]:
        """Parse and interpret the backend-agnostic query parameter models into a dictionary
        that can be used by MongoDB.

        This Mongo-specific method calls the base `EntryCollection.handle_query_params` method
        and adds additional handling of the MongoDB ObjectID type.

        Parameters:
            params: The initialized query parameter model from the server.

        Raises:
            Forbidden: If too large of a page limit is provided.
            BadRequest: If an invalid request is made, e.g., with incorrect fields
                or response format.

        Returns:
            A dictionary representation of the query parameters.

        """
        criteria = super().handle_query_params(params)
        # Handle MongoDB ObjectIDs:
        # - If they were not requested, then explicitly remove them
        # - If they were requested, then cast them to strings in the response
        if "_id" not in criteria.get("projection", {}):
            criteria["projection"]["_id"] = False

        if "page_above" in criteria:
            raise NotImplementedError(
                "`page_above` is not implemented for this backend."
            )

        if criteria.get("projection", {}).get("_id"):
            criteria["projection"]["_id"] = {"$toString": "$_id"}

        return criteria

    def _run_db_query(
        self,
        criteria: Dict[str, Any],
        single_entry: bool = False,
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Run the query on the backend and collect the results.

        Arguments:
            criteria: A dictionary representation of the query parameters.
            single_entry: Whether or not the caller is expecting a single entry response.

        Returns:
            The list of entries from the database (without any re-mapping), the total number of
            entries matching the query and a boolean for whether or not there is more data available.

        """
        results = list(self.collection.find(**criteria))

        if CONFIG.database_backend == SupportedBackend.MONGOMOCK and criteria.get(
            "projection", {}
        ).get("_id"):
            # mongomock does not support `$toString`` in projection, so we have to do it manually
            for ind, doc in enumerate(results):
                results[ind]["_id"] = str(doc["_id"])

        nresults_now = len(results)
        if not single_entry:
            criteria_nolimit = criteria.copy()
            criteria_nolimit.pop("limit", None)
            skip = criteria_nolimit.pop("skip", 0)
            data_returned = self.count(**criteria_nolimit)
            more_data_available = nresults_now + skip < data_returned
        else:
            # SingleEntryQueryParams, e.g., /structures/{entry_id}
            data_returned = nresults_now
            more_data_available = False

        return results, data_returned, more_data_available
