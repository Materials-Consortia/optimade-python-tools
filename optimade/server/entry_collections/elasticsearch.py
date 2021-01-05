import os

from typing import Tuple, List, Union
from fastapi import HTTPException
from elasticsearch_dsl import Search
from elasticsearch.helpers import bulk
import json
import os.path

from optimade.filterparser import LarkParser
from optimade.filtertransformers.elasticsearch import ElasticTransformer, Quantity
from optimade.server.config import CONFIG
from optimade.models import EntryResource
from optimade.server.mappers import BaseResourceMapper
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from .entry_collections import EntryCollection

try:
    CI_FORCE_ELASTIC = bool(int(os.environ.get("OPTIMADE_CI_FORCE_ELASTIC", 0)))
except (TypeError, ValueError):  # pragma: no cover
    CI_FORCE_ELASTIC = False

if CONFIG.database_backend == "elastic" or CI_FORCE_ELASTIC:
    from elasticsearch import Elasticsearch

    client = Elasticsearch()
    print("Using: Real Elastic (elasticsearch)")


with open(os.path.join(os.path.dirname(__file__), "elastic_indexes.json")) as f:
    index_definitions = json.load(f)


class ElasticCollection(EntryCollection):
    def __init__(
        self,
        index: str,
        resource_cls: EntryResource,
        resource_mapper: BaseResourceMapper,
    ):
        super().__init__(resource_cls, resource_mapper)
        self.provider_prefix = CONFIG.provider.prefix
        self.provider_fields = CONFIG.provider_fields.get(resource_mapper.ENDPOINT, [])

        fields = list(self.get_attribute_fields())
        fields.extend(resource_mapper.TOP_LEVEL_NON_ATTRIBUTES_FIELDS)
        fields.extend(
            [f"_{self.provider_prefix}_{field}" for field in self.provider_fields]
        )
        quantities = {}
        for field in fields:
            alias = resource_mapper.alias_for(field)
            length_alias = resource_mapper.length_alias_for(field)

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

        self.parser = LarkParser(
            version=(0, 10, 1), variant="default"
        )  # The ElasticTransformer only supports v0.10.1 as the latest grammar

        self.index = index
        body = index_definitions.get(index, None)
        if body is None:
            body = {
                "mappings": {
                    "doc": {
                        "properties": {
                            resource_mapper.alias_for(field): {"type": "keyword"}
                            for field in fields
                        }
                    }
                }
            }

        client.indices.create(index=self.index, ignore=400, body=body)

    def __len__(self):
        return Search(using=client, index=self.index).execute().hits.total

    def __iter__(self):
        raise NotImplementedError

    def __contains__(self, entry):
        raise NotImplementedError

    def count(self, **kwargs):
        raise NotImplementedError

    def insert(self, data: List[EntryResource]) -> None:
        def get_id(item):
            if self.index == "links":
                id = "%s-%s" % (item["id"], item["type"])
            elif "id" in item:
                id = item["id"]
            elif "_id" in item:
                # use the existing MongoDB ids in the test data
                id = str(item["_id"])
            else:
                # ES will generate ids
                id = None
            item.pop("_id", None)
            return id

        bulk(
            client,
            [
                dict(_index=self.index, _id=get_id(item), _type="doc", _source=item)
                for item in data
            ],
        )

    def find(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> Tuple[List[EntryResource], int, bool, set]:
        search = Search(using=client, index=self.index)

        if getattr(params, "filter", False):
            tree = self.parser.parse(params.filter)
            filter_query = self.transformer.transform(tree)
            search = search.query(filter_query)

        if (
            getattr(params, "response_format", False)
            and params.response_format != "json"
        ):
            raise HTTPException(
                status_code=400, detail="Only 'json' response_format supported"
            )

        if getattr(params, "page_limit", False):
            limit = params.page_limit
            if limit > CONFIG.page_limit_max:
                raise HTTPException(
                    status_code=403,  # Forbidden
                    detail=f"Max allowed page_limit is {CONFIG.page_limit_max}, you requested {limit}",
                )
            per_page = limit
        else:
            per_page = CONFIG.page_limit

        # All OPTIMADE fields
        fields = self.resource_mapper.TOP_LEVEL_NON_ATTRIBUTES_FIELDS.copy()
        fields |= self.get_attribute_fields()
        # All provider-specific fields
        fields |= {
            f"_{self.provider_prefix}_{field_name}"
            for field_name in self.provider_fields
        }
        # The requested fields
        if getattr(params, "response_fields", False):
            fields = set(params.response_fields.split(","))
            fields |= self.resource_mapper.get_required_fields()

        search = search.source(
            includes=[self.resource_mapper.alias_for(field) for field in fields]
        )

        if getattr(params, "sort", False):
            sort = []
            for elt in params.sort.split(","):
                field = elt
                sort_dir = "asc"
                if elt.startswith("-"):
                    field = field[1:]
                    sort_dir = "desc"
                sort.append({field: sort_dir})
            search = search.sort(sort)

        if getattr(params, "page_offset", False):
            page_offset = params.page_offset
        else:
            page_offset = 0

        search = search[page_offset : page_offset + per_page]
        response = search.execute()
        results = [
            self.resource_cls(**self.resource_mapper.map_back(hit.to_dict()))
            for hit in response.hits
        ]

        nresults_now = len(results)
        if isinstance(params, EntryListingQueryParams):
            data_returned = response.hits.total
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

        return results, data_returned, more_data_available, fields
