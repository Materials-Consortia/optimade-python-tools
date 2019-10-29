from abc import abstractmethod
from typing import Collection, Tuple, List, Union

import mongomock
import pymongo.collection
from fastapi import HTTPException
from optimade.filterparser import LarkParser
from optimade.filtertransformers.mongo import MongoTransformer

from .models.util import NonnegativeInt
from .models.entries import EntryResource, EntryResourceAttributes
from .deps import EntryListingQueryParams, SingleEntryQueryParams

from .mappers.structures import StructureMapper


class EntryCollection(Collection):  # pylint: disable=inherit-non-class
    def __init__(
        self,
        collection,
        resource_cls: EntryResource,
        resource_attributes: EntryResourceAttributes,
    ):
        self.collection = collection
        self.parser = LarkParser()
        self.resource_cls = resource_cls
        self.resource_attributes = resource_attributes

    def __len__(self):
        return self.collection.count()

    def __iter__(self):
        return self.collection.find()

    def __contains__(self, entry):
        return self.collection.count(entry) > 0

    @abstractmethod
    def find(
        self, params: EntryListingQueryParams
    ) -> Tuple[List[EntryResource], bool, NonnegativeInt]:
        """
        Fetches results and indicates if more data is available.

        Also gives the total number of data available in the absence of page_limit.

        Args:
            params (EntryListingQueryParams): entry listing URL query params

        Returns:
            Tuple[List[Entry], bool, NonnegativeInt]: (results, more_data_available, data_available)

        """

    def count(self, **kwargs):
        return self.collection.count(**kwargs)


class MongoCollection(EntryCollection):
    def __init__(
        self,
        collection: Union[
            pymongo.collection.Collection, mongomock.collection.Collection
        ],
        resource_cls: EntryResource,
        resource_attributes: EntryResourceAttributes,
        provider: str,
        provider_fields: set,
        page_limit: int,
    ):
        super().__init__(collection, resource_cls, resource_attributes)
        self.transformer = MongoTransformer()
        self.provider = provider
        self.provider_fields = provider_fields
        self.page_limit = page_limit
        self.parser = LarkParser(
            version=(0, 9, 7)
        )  # The MongoTransformer only supports v0.9.7 as the latest grammar

    def __len__(self):
        return self.collection.estimated_document_count()

    def __contains__(self, entry):
        return self.collection.count_documents(entry.dict()) > 0

    def count(self, **kwargs):
        for k in list(kwargs.keys()):
            if k not in ("filter", "skip", "limit", "hint", "maxTimeMS"):
                del kwargs[k]
        return self.collection.count_documents(**kwargs)

    def find(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> Tuple[List[EntryResource], bool, NonnegativeInt]:
        criteria = self._parse_params(params)
        if isinstance(params, EntryListingQueryParams):
            criteria_nolimit = criteria.copy()
            del criteria_nolimit["limit"]
            nresults_now = self.count(**criteria)
            nresults_total = self.count(**criteria_nolimit)
            more_data_available = nresults_now < nresults_total
            data_available = nresults_total
        else:
            more_data_available = False
            data_available = self.count(**criteria)
            if data_available != 1:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instead of a single entry, {data_available} entries were found",
                )
        results = []
        for doc in self.collection.find(**criteria):
            results.append(self.resource_cls(**StructureMapper.map_back(doc)))
        if isinstance(params, SingleEntryQueryParams):
            results = results[0]

        return results, more_data_available, data_available

    def _alias_filter(self, filter_: dict) -> dict:
        res = {}
        for key, value in filter_.items():
            new_value = value
            if isinstance(value, dict):
                new_value = self._alias_filter(value)
            res[StructureMapper.alias_for(key)] = new_value
        return res

    def _parse_params(self, params: EntryListingQueryParams) -> dict:
        cursor_kwargs = {}

        if getattr(params, "filter", False):
            tree = self.parser.parse(params.filter)
            mongo_filter = self.transformer.transform(tree)
            cursor_kwargs["filter"] = self._alias_filter(mongo_filter)
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
            limit = self.page_limit
            if params.page_limit != self.page_limit:
                limit = params.page_limit
            if limit > self.page_limit:
                raise HTTPException(
                    status_code=400, detail=f"Max page_limit is {self.page_limit}"
                )
            if limit == 0:
                limit = self.page_limit
            cursor_kwargs["limit"] = limit

        if getattr(params, "response_fields", False):
            fields = set(params.response_fields.split(","))
        else:
            # All OPTiMaDe fields
            fields = {"id", "type"}
            fields |= set(self.resource_attributes.__fields__.keys())
            # All provider-specific fields
            fields |= {self.provider + _ for _ in self.provider_fields}
        cursor_kwargs["projection"] = [StructureMapper.alias_for(f) for f in fields]

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
