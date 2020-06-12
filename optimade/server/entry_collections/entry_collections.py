from abc import abstractmethod
from typing import Collection, Tuple, List

from optimade.server.mappers import BaseResourceMapper
from optimade.models import EntryResource
from optimade.filterparser import LarkParser
from optimade.server.query_params import EntryListingQueryParams
from optimade.server.config import CONFIG


def create_collection(
    name: str, resource_cls: EntryResource, resource_mapper: BaseResourceMapper
):
    if CONFIG.database_backend == "mongo":
        from .mongo import MongoCollection

        return MongoCollection(
            name=name, resource_cls=resource_cls, resource_mapper=resource_mapper,
        )

    if CONFIG.database_backend == "elastic":
        from .elasticsearch import ElasticCollection

        return ElasticCollection(
            index=name, resource_cls=resource_cls, resource_mapper=resource_mapper,
        )

    raise NotImplementedError(
        "The database backend %s is not implemented" % CONFIG.database_backend
    )


class EntryCollection(Collection):  # pylint: disable=inherit-non-class
    def __init__(
        self, resource_cls: EntryResource, resource_mapper: BaseResourceMapper,
    ):
        self.parser = LarkParser()
        self.resource_cls = resource_cls
        self.resource_mapper = resource_mapper

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def __iter__(self):
        pass

    @abstractmethod
    def __contains__(self, entry):
        pass

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
    def insert(self, data: List[EntryResource]) -> None:
        """
        Adds the given items to the underlying database.

        Args:
            data List[EntryResource]: The items as a list of optimade entry resources.
        """

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

    @abstractmethod
    def count(self, **kwargs):
        pass
