from abc import abstractmethod, ABC
from typing import Tuple, List, Union
import warnings
import re

from lark import Transformer

from optimade.filterparser import LarkParser
from optimade.models import EntryResource
from optimade.server.config import CONFIG
from optimade.server.exceptions import BadRequest, Forbidden
from optimade.server.mappers import BaseResourceMapper
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.warnings import FieldValueNotRecognized


class EntryCollection(ABC):
    """ Backend-agnostic base class for querying collections of
    [`EntryResource`][optimade.models.entries.EntryResource]s. """

    def __init__(
        self,
        collection,
        resource_cls: EntryResource,
        resource_mapper: BaseResourceMapper,
        transformer: Transformer,
    ):
        """ Initialize the collection for the given parameters.

        Parameters:
            collection: The backend-specific collection.
            resource_cls (EntryResource): The `EntryResource` model
                that is stored by the collection.
            resource_mapper (BaseResourceMapper): A resource mapper
                object that handles aliases and format changes between
                deserialization and response.
            transformer (Transformer): The Lark `Transformer` used to
                interpret the filter.

        """
        self.collection = collection
        self.parser = LarkParser()
        self.resource_cls = resource_cls
        self.resource_mapper = resource_mapper
        self.transformer = transformer

        self.provider_prefix = CONFIG.provider.prefix
        self.provider_fields = CONFIG.provider_fields.get(resource_mapper.ENDPOINT, [])

    @abstractmethod
    def __len__(self) -> int:
        """ Returns the total number of entries in the collection. """

    @abstractmethod
    def count(self, **kwargs) -> int:
        """ Returns the number of entries matching the query specified
        by the keyword arguments.

        Parameters:
            kwargs (dict): Query parameters as keyword arguments.

        """

    @abstractmethod
    def find(
        self, params: EntryListingQueryParams
    ) -> Tuple[List[EntryResource], int, bool, set]:
        """
        Fetches results and indicates if more data is available.

        Also gives the total number of data available in the absence of `page_limit`.
        See [`EntryListingQueryParams`][optimade.server.query_params.EntryListingQueryParams]
        for more information.

        Parameters:
            params (EntryListingQueryParams): entry listing URL query params

        Returns:
            (`results`, `data_returned`, `more_data_available`, `fields`).

        """

    @property
    def all_fields(self) -> set:
        """ Get the set of all fields handled in this collection, from
        attribute fields in the schema, provider fields and top-level
        OPTIMADE fields.

    Returns:
        set: All fields handled in this collection.

        """
        # All OPTIMADE fields
        fields = self.resource_mapper.TOP_LEVEL_NON_ATTRIBUTES_FIELDS.copy()
        fields |= self.get_attribute_fields()
        # All provider-specific fields
        fields |= {
            f"_{self.provider_prefix}_{field_name}"
            for field_name in self.provider_fields
        }

        return fields

    def get_attribute_fields(self) -> set:
        """ Get the set of attribute fields from the schema of the
        resource class, resolving references along the way.

        Returns:
            set: Property names.

        """
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

    def handle_query_params(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> dict:
        """ Parse and interpret the backend-agnostic query parameter models into a dictionary
        that can be used by the specific backend.

        Note:
            Currently this method returns the pymongo interpretation of the parameters,
            which will need modification for modified for other backends.

        Parameters:
            params (Union[EntryListingQueryParams, SingleEntryQueryParams]): The initialized query parameter model from the server.

        Raises:
            Forbidden: If too large of a page limit is provided.
            BadRequest: If an invalid request is made, e.g., with incorrect fields
                or response format.

        Returns:
            dict: A dictionary representation of the query parameters, ready to be used
                by pymongo.

        """
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
            raise BadRequest(
                detail=f"Response format {params.response_format} is not supported, please use response_format='json'"
            )

        if getattr(params, "page_limit", False):
            limit = params.page_limit
            if limit > CONFIG.page_limit_max:
                raise Forbidden(
                    detail=f"Max allowed page_limit is {CONFIG.page_limit_max}, you requested {limit}",
                )
            cursor_kwargs["limit"] = limit
        else:
            cursor_kwargs["limit"] = CONFIG.page_limit

        cursor_kwargs["fields"] = self.all_fields
        cursor_kwargs["projection"] = [
            self.resource_mapper.alias_for(f) for f in self.all_fields
        ]

        if getattr(params, "sort", False):
            cursor_kwargs["sort"] = self.parse_sort_params(params.sort)

        if getattr(params, "page_offset", False):
            cursor_kwargs["skip"] = params.page_offset

        return cursor_kwargs

    def parse_sort_params(self, sort_params) -> List[Tuple[str, int]]:
        """ Handles any sort parameters passed to the collection,
        resolving aliases and dealing with any invalid fields.

        Raises:
            BadRequest: if an invalid sort is requested.

        Returns:
            A list of tuples containing the aliased field name and
            sort direction encoded as 1 (ascending) or -1 (descending).

        """
        sort_spec = []
        for field in sort_params.split(","):
            sort_dir = 1
            if field.startswith("-"):
                field = field[1:]
                sort_dir = -1
            aliased_field = self.resource_mapper.alias_for(field)
            sort_spec.append((aliased_field, sort_dir))

        unknown_fields = [
            field
            for field, _ in sort_spec
            if self.resource_mapper.alias_of(field) not in self.all_fields
        ]

        if unknown_fields:
            error_detail = "Unable to sort on unknown field{} '{}'".format(
                "s" if len(unknown_fields) > 1 else "", "', '".join(unknown_fields),
            )

            # If all unknown fields are "other" provider-specific, then only provide a warning
            if all(
                (
                    re.match(r"_[a-z_0-9]+_[a-z_0-9]*", field)
                    and not field.startswith(f"_{self.provider_prefix}_")
                )
                for field in unknown_fields
            ):
                warnings.warn(error_detail, FieldValueNotRecognized)

            # Otherwise, if all fields are unknown, or some fields are unknown and do not
            # have other provider prefixes, then return 400: Bad Request
            else:
                raise BadRequest(detail=error_detail)

        # If at least one valid field has been provided for sorting, then use that
        sort_spec = tuple(
            (field, sort_dir)
            for field, sort_dir in sort_spec
            if field not in unknown_fields
        )

        return sort_spec
