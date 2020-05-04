import os

from typing import Tuple, List, Union
import mongomock
import pymongo.collection
from fastapi import HTTPException

from optimade.filterparser import LarkParser
from optimade.filtertransformers.mongo import MongoTransformer
from optimade.server.config import CONFIG
from optimade.models import EntryResource
from optimade.server.mappers import BaseResourceMapper
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from .entry_collections import EntryCollection

try:
    CI_FORCE_MONGO = bool(int(os.environ.get("OPTIMADE_CI_FORCE_MONGO", 0)))
except (TypeError, ValueError):  # pragma: no cover
    CI_FORCE_MONGO = False


if CONFIG.use_real_mongo or CI_FORCE_MONGO:
    from pymongo import MongoClient

    client = MongoClient(CONFIG.mongo_uri)
    print("Using: Real MongoDB (pymongo)")
else:
    from mongomock import MongoClient

    client = MongoClient()
    print("Using: Mock MongoDB (mongomock)")


class MongoCollection(EntryCollection):
    def __init__(
        self,
        collection: Union[
            pymongo.collection.Collection, mongomock.collection.Collection
        ],
        resource_cls: EntryResource,
        resource_mapper: BaseResourceMapper,
    ):
        super().__init__(collection, resource_cls, resource_mapper)
        self.transformer = MongoTransformer(mapper=resource_mapper)

        self.provider_prefix = CONFIG.provider.prefix
        self.provider_fields = CONFIG.provider_fields.get(resource_mapper.ENDPOINT, [])
        self.parser = LarkParser(
            version=(0, 10, 1), variant="default"
        )  # The MongoTransformer only supports v0.10.1 as the latest grammar

        # check aliases do not clash with mongo operators
        self._check_aliases(self.resource_mapper.all_aliases())
        self._check_aliases(self.resource_mapper.all_length_aliases())

    def __len__(self):
        return self.collection.estimated_document_count()

    def __contains__(self, entry):
        return self.collection.count_documents(entry.dict()) > 0

    def count(self, **kwargs):
        for k in list(kwargs.keys()):
            if k not in ("filter", "skip", "limit", "hint", "maxTimeMS"):
                del kwargs[k]
        if "filter" not in kwargs:  # "filter" is needed for count_documents()
            kwargs["filter"] = {}
        return self.collection.count_documents(**kwargs)

    def find(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> Tuple[List[EntryResource], int, bool, set]:
        criteria = self._parse_params(params)

        all_fields = criteria.pop("fields")
        if getattr(params, "response_fields", False):
            fields = set(params.response_fields.split(","))
            fields |= self.resource_mapper.get_required_fields()
        else:
            fields = all_fields.copy()

        results = []
        for doc in self.collection.find(**criteria):
            results.append(self.resource_cls(**self.resource_mapper.map_back(doc)))

        nresults_now = len(results)
        if isinstance(params, EntryListingQueryParams):
            criteria_nolimit = criteria.copy()
            criteria_nolimit.pop("limit", None)
            data_returned = self.count(**criteria_nolimit)
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

        return results, data_returned, more_data_available, all_fields - fields

    def _parse_params(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> dict:
        cursor_kwargs = {}

        if getattr(params, "filter", False):
            tree = self.parser.parse(params.filter)
            cursor_kwargs["filter"] = self.transformer.transform(tree)
        else:
            cursor_kwargs["filter"] = {}

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
            cursor_kwargs["limit"] = limit
        else:
            cursor_kwargs["limit"] = CONFIG.page_limit

        # All OPTIMADE fields
        fields = self.resource_mapper.TOP_LEVEL_NON_ATTRIBUTES_FIELDS.copy()
        fields |= self.get_attribute_fields()
        # All provider-specific fields
        fields |= {
            f"_{self.provider_prefix}_{field_name}"
            for field_name in self.provider_fields
        }
        cursor_kwargs["fields"] = fields
        cursor_kwargs["projection"] = [
            self.resource_mapper.alias_for(f) for f in fields
        ]

        if getattr(params, "sort", False):
            sort_spec = []
            for elt in params.sort.split(","):
                field = elt
                sort_dir = 1
                if elt.startswith("-"):
                    field = field[1:]
                    sort_dir = -1
                sort_spec.append((field, sort_dir))
            cursor_kwargs["sort"] = sort_spec

        if getattr(params, "page_offset", False):
            cursor_kwargs["skip"] = params.page_offset

        return cursor_kwargs

    def _check_aliases(self, aliases):
        """ Check that aliases do not clash with mongo keywords. """
        if any(
            alias[0].startswith("$") or alias[1].startswith("$") for alias in aliases
        ):
            raise RuntimeError(f"Cannot define an alias starting with a '$': {aliases}")
