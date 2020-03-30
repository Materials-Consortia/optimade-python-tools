from abc import abstractmethod
from typing import Collection, Tuple, List

from optimade.server.mappers import BaseResourceMapper
from optimade.filterparser import LarkParser
from optimade.models import EntryResource
from optimade.server.query_params import EntryListingQueryParams


class EntryCollection(Collection):  # pylint: disable=inherit-non-class
    def __init__(
        self,
        collection,
        resource_cls: EntryResource,
        resource_mapper: BaseResourceMapper,
    ):
        self.collection = collection
        self.parser = LarkParser()
        self.resource_cls = resource_cls
        self.resource_mapper = resource_mapper

    def __len__(self):
        return self.collection.count()

    def __iter__(self):
        return self.collection.find()

    def __contains__(self, entry):
        return self.collection.count(entry) > 0

    def get_attribute_fields(self) -> set:
        schema = self.resource_cls.schema()
        attributes = schema["properties"]["attributes"]
        if "allOf" in attributes:
            allOf = attributes.pop("allOf")
            for dict_ in allOf:
                attributes.update(dict_)
        if "$ref" in attributes:
            path = attributes["$ref"].split("/")[1:]
            attributes = schema.copy()
            while path:
                next_key = path.pop(0)
                attributes = attributes[next_key]
        return set(attributes["properties"].keys())

    @abstractmethod
    def find(
        self, params: EntryListingQueryParams
    ) -> Tuple[List[EntryResource], int, bool, set]:
        """
        Fetches results and indicates if more data is available.

        Also gives the total number of data available in the absence of page_limit.

        Args:
            params (EntryListingQueryParams): entry listing URL query params

        Returns:
            Tuple[List[Entry], int, bool, set]: (results, data_returned, more_data_available, fields)

        """

    def count(self, **kwargs):
        return self.collection.count(**kwargs)
