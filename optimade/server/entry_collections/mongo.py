from typing import Any, Optional, Union

from optimade.filtertransformers.mongo import MongoTransformer
from optimade.models import EntryResource
from optimade.server.config import CONFIG, SupportedBackend
from optimade.server.entry_collections import EntryCollection
from optimade.server.logger import LOGGER
from optimade.server.mappers import BaseResourceMapper
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams

if CONFIG.database_backend.value == "mongodb":
    from pymongo import MongoClient, version_tuple
    from pymongo.errors import ExecutionTimeout

    if version_tuple[0] < 4:
        LOGGER.warning(
            "Support for pymongo<=3 (and thus MongoDB v3) is deprecated and will be "
            "removed in the next minor release."
        )

    LOGGER.info("Using: Real MongoDB (pymongo)")

elif CONFIG.database_backend.value == "mongomock":
    from mongomock import MongoClient

    LOGGER.info("Using: Mock MongoDB (mongomock)")

if CONFIG.database_backend.value in ("mongomock", "mongodb"):
    CLIENT = MongoClient(CONFIG.mongo_uri)


class MongoCollection(EntryCollection):
    """Class for querying MongoDB collections (implemented by either pymongo or mongomock)
    containing serialized [`EntryResource`][optimade.models.entries.EntryResource]s objects.

    """

    def __init__(
        self,
        name: str,
        resource_cls: type[EntryResource],
        resource_mapper: type[BaseResourceMapper],
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

    def count(self, **kwargs: Any) -> Union[int, None]:
        """Returns the number of entries matching the query specified
        by the keyword arguments, or `None` if the count timed out.

        Parameters:
            **kwargs: Query parameters as keyword arguments. The keys
                'filter', 'skip', 'limit', 'hint' and 'maxTimeMS' will be passed
                to the `pymongo.collection.Collection.count_documents` method.

        """
        for k in list(kwargs.keys()):
            if k not in ("filter", "skip", "limit", "hint", "maxTimeMS"):
                del kwargs[k]
        if "filter" not in kwargs:
            return self.collection.estimated_document_count()
        else:
            if "maxTimeMS" not in kwargs:
                kwargs["maxTimeMS"] = 1000 * CONFIG.mongo_count_timeout
            try:
                return self.collection.count_documents(**kwargs)
            except ExecutionTimeout:
                return None

    def insert(self, data: list[EntryResource]) -> None:
        """Add the given entries to the underlying database.

        Warning:
            No validation is performed on the incoming data.

        Arguments:
            data: The entry resource objects to add to the database.

        """
        self.collection.insert_many(data)

    def handle_query_params(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> dict[str, Any]:
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
        self, criteria: dict[str, Any], single_entry: bool = False
    ) -> tuple[list[dict[str, Any]], Optional[int], bool]:
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
            # Only correct most of the time: if the total number of remaining results is exactly the page limit
            # then this will incorrectly say there is more_data_available
            if data_returned is None:
                more_data_available = nresults_now == criteria.get("limit", 0)
            else:
                more_data_available = nresults_now + skip < data_returned
        else:
            # SingleEntryQueryParams, e.g., /structures/{entry_id}
            data_returned = nresults_now
            more_data_available = False

        return results, data_returned, more_data_available

    def _check_aliases(self, aliases):
        """Check that aliases do not clash with mongo keywords."""
        if any(
            alias[0].startswith("$") or alias[1].startswith("$") for alias in aliases
        ):
            raise RuntimeError(f"Cannot define an alias starting with a '$': {aliases}")
