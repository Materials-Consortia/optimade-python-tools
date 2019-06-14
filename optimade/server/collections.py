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
from .models.modified_jsonapi import Resource
from .models.structures import StructureMapper
from .deps import EntryListingQueryParams


config = ConfigParser()
config.read(Path(__file__).resolve().parent.joinpath("config.ini"))
RESPONSE_LIMIT = config["DEFAULT"].getint("RESPONSE_LIMIT")


class EntryCollection(Collection):
    def __init__(self, collection, resource_cls: Resource):
        self.collection = collection
        self.parser = LarkParser()
        self.resource_cls = resource_cls

    def __len__(self):
        return self.collection.count()

    def __iter__(self):
        return self.collection.find()

    def __contains__(self, entry):
        return self.collection.count(entry) > 0

    @abstractmethod
    def find(
        self, params: EntryListingQueryParams
    ) -> Tuple[List[Resource], bool, NonnegativeInt]:
        """
        Fetches results and indicates if more data is available.

        Also gives the total number of data available in the absence of response_limit.

        Args:
            params (EntryListingQueryParams): entry listing URL query params

        Returns:
            Tuple[List[Entry], bool, NonnegativeInt]: (results, more_data_available, data_available)

        """
        pass

    def count(self, **kwargs):
        return self.collection.count(**kwargs)


class MongoCollection(EntryCollection):
    def __init__(
        self,
        collection: Union[
            pymongo.collection.Collection, mongomock.collection.Collection
        ],
        resource_cls: Resource,
    ):
        super().__init__(collection, resource_cls)
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
    ) -> Tuple[List[Resource], bool, NonnegativeInt]:
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

        if params.response_format and params.response_format != "jsonapi":
            raise HTTPException(
                status_code=400, detail="Only 'jsonapi' response_format supported"
            )

        limit = RESPONSE_LIMIT
        if params.response_limit != RESPONSE_LIMIT:
            limit = params.response_limit
        elif params.page_limit != RESPONSE_LIMIT:
            limit = params.page_limit
        if limit > RESPONSE_LIMIT:
            raise HTTPException(
                status_code=400,
                detail=f"Max response_limit/page[limit] is {RESPONSE_LIMIT}",
            )
        elif limit == 0:
            limit = RESPONSE_LIMIT
        cursor_kwargs["limit"] = limit

        fields = {"id", "local_id", "last_modified"}
        if params.response_fields:
            fields |= set(params.response_fields.split(","))
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
