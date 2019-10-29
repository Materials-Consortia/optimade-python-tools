from abc import abstractmethod
from configparser import ConfigParser
from pathlib import Path
from typing import Collection, Tuple, List, Union

import mongomock
import pymongo.collection
from fastapi import HTTPException
from optimade.filterparser import LarkParser
from optimade.filtertransformers.mongo import MongoTransformer

from .models.util import NonnegativeInt
from .models.entries import EntryResource, EntryResourceAttributes
from .deps import EntryListingQueryParams

from .mappers.structures import StructureMapper


config = ConfigParser()
config.read(Path(__file__).resolve().parent.joinpath("config.ini"))
PAGE_LIMIT = config["DEFAULT"].getint("PAGE_LIMIT")
PROVIDER = config["DEFAULT"].get("PROVIDER")
PROVIDER_FIELDS = {field for field, _ in config["STRUCTURE"].items() if _ == ""}


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
    ):
        super().__init__(collection, resource_cls, resource_attributes)
        self.transformer = MongoTransformer()

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
        self, params: EntryListingQueryParams
    ) -> Tuple[List[EntryResource], bool, NonnegativeInt]:
        criteria = self._parse_params(params)
        criteria_nolimit = criteria.copy()
        del criteria_nolimit["limit"]
        nresults_now = self.count(**criteria)
        nresults_total = self.count(**criteria_nolimit)
        more_data_available = nresults_now < nresults_total
        data_available = nresults_total
        results = []
        for doc in self.collection.find(**criteria):
            results.append(self.resource_cls(**StructureMapper.map_back(doc)))
        return results, more_data_available, data_available

    def _parse_params(self, params: EntryListingQueryParams) -> dict:
        cursor_kwargs = {}

        if params.filter:
            tree = self.parser.parse(params.filter)
            cursor_kwargs["filter"] = self.transformer.transform(tree)
        else:
            cursor_kwargs["filter"] = {}

        if params.response_format and params.response_format != "json":
            raise HTTPException(
                status_code=400, detail="Only 'json' response_format supported"
            )

        limit = PAGE_LIMIT
        if params.page_limit != PAGE_LIMIT:
            limit = params.page_limit
        elif params.page_limit != PAGE_LIMIT:
            limit = params.page_limit
        if limit > PAGE_LIMIT:
            raise HTTPException(
                status_code=400, detail=f"Max page_limit is {PAGE_LIMIT}"
            )
        if limit == 0:
            limit = PAGE_LIMIT
        cursor_kwargs["limit"] = limit

        if params.response_fields:
            fields = set(params.response_fields.split(","))
        else:
            # All OPTiMaDe fields
            fields = {"id", "type"}
            try:
                fields |= set(self.resource_attributes.__fields__.keys())
            except AttributeError:
                fields |= set(self.resource_attributes.__annotations__.keys())
            # All provider-specific fields
            fields |= {PROVIDER + _ for _ in PROVIDER_FIELDS}
        cursor_kwargs["projection"] = [StructureMapper.alias_for(f) for f in fields]

        if params.sort:
            sort_spec = []
            for elt in params.sort.split(","):
                field = elt
                sort_dir = 1
                if elt.startswith("-"):
                    field = field[1:]
                    sort_dir = -1
                sort_spec.append((field, sort_dir))
            cursor_kwargs["sort"] = sort_spec

        if params.page_offset:
            cursor_kwargs["skip"] = params.page_offset

        return cursor_kwargs
