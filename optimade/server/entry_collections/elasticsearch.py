import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Optional

from optimade.filtertransformers.elasticsearch import ElasticTransformer
from optimade.models import EntryResource
from optimade.server.config import CONFIG
from optimade.server.entry_collections import EntryCollection, PaginationMechanism
from optimade.server.logger import LOGGER
from optimade.server.mappers import BaseResourceMapper

if CONFIG.database_backend.value == "elastic":
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk
    from elasticsearch_dsl import Search

    CLIENT = Elasticsearch(hosts=CONFIG.elastic_hosts)
    LOGGER.info("Using: Elasticsearch backend at %s", CONFIG.elastic_hosts)


class ElasticCollection(EntryCollection):
    pagination_mechanism = PaginationMechanism("page_offset")

    def __init__(
        self,
        name: str,
        resource_cls: type[EntryResource],
        resource_mapper: type[BaseResourceMapper],
        client: Optional["Elasticsearch"] = None,
    ):
        """Initialize the ElasticCollection for the given parameters.

        Parameters:
            name: The name of the collection.
            resource_cls: The type of entry resource that is stored by the collection.
            resource_mapper: A resource mapper object that handles aliases and
                format changes between deserialization and response.
            client: A preconfigured Elasticsearch client.

        """
        super().__init__(
            resource_cls=resource_cls,
            resource_mapper=resource_mapper,
            transformer=ElasticTransformer(mapper=resource_mapper),
        )

        self.client = client if client else CLIENT
        self.name = name

    def count(self, *args, **kwargs) -> int:
        raise NotImplementedError

    def create_default_index(self) -> None:
        """Create the default index for the collection.

        For Elastic, the default is to create a search index
        over all relevant OPTIMADE fields based on the configured
        mapper.

        """
        return self.create_optimade_index()

    def create_optimade_index(self) -> None:
        """Load or create an index that can handle aliased OPTIMADE fields and attach it
        to the current client.

        """
        body = self.predefined_index.get(self.name)
        if body is None:
            body = self.create_elastic_index_from_mapper(
                self.resource_mapper, self.all_fields
            )

        properties = {}
        for field in list(body["mappings"]["properties"].keys()):
            properties[self.resource_mapper.get_backend_field(field)] = body[
                "mappings"
            ]["properties"].pop(field)
        properties["id"] = {"type": "keyword"}
        body["mappings"]["properties"] = properties
        self.client.indices.create(index=self.name, ignore=400, **body)

        LOGGER.debug(f"Created Elastic index for {self.name!r} with parameters {body}")

    @property
    def predefined_index(self) -> dict[str, Any]:
        """Loads and returns the default pre-defined index."""
        with open(Path(__file__).parent.joinpath("elastic_indexes.json")) as f:
            index = json.load(f)
        return index

    @staticmethod
    def create_elastic_index_from_mapper(
        resource_mapper: type[BaseResourceMapper], fields: Iterable[str]
    ) -> dict[str, Any]:
        """Create a fallback elastic index based on a resource mapper.

        Arguments:
            resource_mapper: The resource mapper to create the index for.
            fields: The list of fields to use in the index.

        Returns:
            The parameters to pass to `client.indices.create(...)` (previously
                the 'body' parameters).

        """
        properties = {
            resource_mapper.get_optimade_field(field): {"type": "keyword"}
            for field in fields
        }
        properties["id"] = {"type": "keyword"}
        return {"mappings": {"properties": properties}}

    def __len__(self):
        """Returns the total number of entries in the collection."""
        return Search(using=self.client, index=self.name).execute().hits.total.value

    def insert(self, data: list[EntryResource | dict]) -> None:
        """Add the given entries to the underlying database.

        Warning:
            No validation is performed on the incoming data.

        Arguments:
            data: The entry resource objects to add to the database.

        """

        def get_id(item):
            if self.name == "links":
                id_ = f"{item['id']}-{item['type']}"
            elif "id" in item:
                id_ = item["id"]
            elif "_id" in item:
                # use the existing MongoDB ids in the test data
                id_ = str(item["_id"])
            else:
                # ES will generate ids
                id_ = None
            item.pop("_id", None)
            return id_

        bulk(
            self.client,
            (
                {
                    "_index": self.name,
                    "_id": get_id(item),
                    "_source": item,
                }
                for item in data
            ),
        )

    def _run_db_query(
        self, criteria: dict[str, Any], single_entry=False
    ) -> tuple[list[dict[str, Any]], int, bool]:
        """Run the query on the backend and collect the results.

        Arguments:
            criteria: A dictionary representation of the query parameters.
            single_entry: Whether or not the caller is expecting a single entry response.

        Returns:
            The list of entries from the database (without any re-mapping), the total number of
            entries matching the query and a boolean for whether or not there is more data available.

        """

        search = Search(using=self.client, index=self.name)

        if criteria.get("filter", False):
            search = search.query(criteria["filter"])

        page_offset = criteria.get("skip", None)
        page_above = criteria.get("page_above", None)

        limit = criteria.get("limit", CONFIG.page_limit)

        all_aliased_fields = [
            self.resource_mapper.get_backend_field(field) for field in self.all_fields
        ]
        search = search.source(includes=all_aliased_fields)

        elastic_sort = [
            {field: {"order": "desc" if sort_dir == -1 else "asc"}}
            for field, sort_dir in criteria.get("sort", {})
        ]
        if not elastic_sort:
            elastic_sort = [
                {self.resource_mapper.get_backend_field("id"): {"order": "asc"}}
            ]

        search = search.sort(*elastic_sort)

        if page_offset:
            search = search[page_offset : page_offset + limit]

        elif page_above:
            search = search.extra(search_after=page_above, limit=limit)

        else:
            search = search[0:limit]
            page_offset = 0

        search = search.extra(track_total_hits=True)
        response = search.execute()

        results = [hit.to_dict() for hit in response.hits]

        more_data_available = False
        if not single_entry:
            data_returned = response.hits.total.value
            if page_above is not None:
                more_data_available = len(results) == limit and data_returned != limit
            else:
                more_data_available = page_offset + limit < data_returned
        else:
            # SingleEntryQueryParams, e.g., /structures/{entry_id}
            data_returned = len(results)

        return results, data_returned, more_data_available
