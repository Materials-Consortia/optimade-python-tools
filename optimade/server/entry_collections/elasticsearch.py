import os

from pathlib import Path

from typing import Tuple, List, Optional, Dict, Any, Iterable, Union
from fastapi import HTTPException
from elasticsearch_dsl import Search
from elasticsearch.helpers import bulk
import json
import os.path

from optimade.filterparser import LarkParser
from optimade.filtertransformers.elasticsearch import ElasticTransformer, Quantity
from optimade.server.config import CONFIG
from optimade.server.logger import LOGGER
from optimade.models import EntryResource
from optimade.server.mappers import BaseResourceMapper
from .entry_collections import EntryCollection

try:
    CI_FORCE_ELASTIC = bool(int(os.environ.get("OPTIMADE_CI_FORCE_ELASTIC", 0)))
except (TypeError, ValueError):  # pragma: no cover
    CI_FORCE_ELASTIC = False

if CONFIG.database_backend.value == "elastic" or CI_FORCE_ELASTIC:
    from elasticsearch import Elasticsearch

    CLIENT = Elasticsearch(hosts=CONFIG.elastic_hosts)
    print("Using: Real Elastic (elasticsearch)")


with open(Path(__file__).parent.joinpath("elastic_indexes.json")) as f:
    INDEX_DEFINITIONS = json.load(f)


class ElasticCollection(EntryCollection):
    def __init__(
        self,
        name: str,
        resource_cls: EntryResource,
        resource_mapper: BaseResourceMapper,
        client: Optional[Elasticsearch] = None,
    ):
        """Initialize the ElasticCollection for the given parameters.

        Parameters:
            name: The name of the collection.
            resource_cls: The type of entry resource that is stored by the collection.
            resource_mapper: A resource mapper object that handles aliases and
                format changes between deserialization and response.
            client: A preconfigured Elasticsearch client.

        """
        self.client = CLIENT
        if client:
            self.client = client

        self.resource_cls = resource_cls
        self.resource_mapper = resource_mapper
        self.provider_prefix = CONFIG.provider.prefix
        self.provider_fields = CONFIG.provider_fields.get(resource_mapper.ENDPOINT, [])
        self.parser = LarkParser()

        quantities = {}
        for field in self.all_fields:
            alias = self.resource_mapper.alias_for(field)
            length_alias = self.resource_mapper.length_alias_for(field)

            quantities[field] = Quantity(name=field, es_field=alias)
            if length_alias is not None:
                quantities[length_alias] = Quantity(name=length_alias)
                quantities[field].length_quantity = quantities[length_alias]

        if "elements" in quantities:
            quantities["elements"].has_only_quantity = Quantity(name="elements_only")
            quantities["elements"].nested_quantity = quantities["elements_ratios"]

        if "elements_ratios" in quantities:
            quantities["elements_ratios"].nested_quantity = quantities[
                "elements_ratios"
            ]

        self.transformer = ElasticTransformer(quantities=quantities.values())

        self.name = name
        body = INDEX_DEFINITIONS.get(name)
        if body is None:
            body = self.create_elastic_index_from_mapper(
                resource_mapper, self.all_fields
            )

        self.client.indices.create(index=self.name, ignore=400)

        LOGGER.info(f"Created index for {self.name!r} with body {body}")

    @staticmethod
    def create_elastic_index_from_mapper(
        resource_mapper: BaseResourceMapper, fields: Iterable[str]
    ) -> Dict[str, Any]:
        """Create a fallback elastic index based on a resource mapper.

        Arguments:
            resource_mapper: The resource mapper to create the index for.
            fields: The list of fields to use in the index.

        Returns:
            The `body` parameter to pass to `client.indices.create(..., body=...)`.

        """
        return {
            "mappings": {
                "doc": {
                    "properties": {
                        resource_mapper.alias_for(field): {"type": "keyword"}
                        for field in fields
                    }
                }
            }
        }

    def __len__(self):
        return Search(using=self.client, index=self.name).execute().hits.total.value

    def __iter__(self):
        raise NotImplementedError

    def __contains__(self, entry):
        raise NotImplementedError

    def count(self, **kwargs):
        raise NotImplementedError

    def insert(self, data: List[EntryResource]) -> None:
        def get_id(item):
            if self.name == "links":
                id_ = "%s-%s" % (item["id"], item["type"])
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
            [dict(_index=self.name, _id=get_id(item), _source=item) for item in data],
        )

    def _run_db_query(
        self, criteria: Dict[str, Any], single_entry=False
    ) -> Tuple[Union[List[Dict[str, Any]], Dict[str, Any]], int, bool]:
        """Execute the query on the Elasticsearch backend."""

        search = Search(using=self.client, index=self.name)

        page_offset = criteria.get("skip", 0)
        limit = criteria.get("limit", CONFIG.page_limit)

        search = search.source(includes=self.all_fields)

        sort_spec = criteria.get("sort", [])
        if sort_spec:
            sort_spec = [{field: sort_dir} for field, sort_dir in sort_spec]
            search = search.sort(sort_spec)

        search = search[page_offset : page_offset + limit]
        response = search.execute()

        results = [hit.to_dict() for hit in response.hits]

        nresults_now = len(results)
        if not single_entry:
            data_returned = response.hits.total.value
            more_data_available = nresults_now < data_returned
        else:
            # SingleEntryQueryParams, e.g., /structures/{entry_id}
            data_returned = nresults_now
            more_data_available = False
            if nresults_now > 1:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instead of a single entry, {nresults_now} entries were found",
                )
            results = results[0] if results else None

        return results, data_returned, more_data_available
