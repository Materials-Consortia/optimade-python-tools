import enum
import re
import warnings
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, Optional, Union

from lark import Transformer

from optimade.exceptions import BadRequest, Forbidden, NotFound
from optimade.filterparser import LarkParser
from optimade.models import Attributes, EntryResource
from optimade.models.types import NoneType, _get_origin_type
from optimade.server.config import CONFIG, SupportedBackend
from optimade.server.mappers import BaseResourceMapper
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.warnings import (
    FieldValueNotRecognized,
    QueryParamNotUsed,
    UnknownProviderProperty,
)


def create_collection(
    name: str,
    resource_cls: type[EntryResource],
    resource_mapper: type[BaseResourceMapper],
) -> "EntryCollection":
    """Create an `EntryCollection` of the configured type, depending on the value of
    `CONFIG.database_backend`.

    Arguments:
        name: The collection name.
        resource_cls: The type of entry resource to be stored within the collection.
        resource_mapper: The associated resource mapper for that entry resource type.

    Returns:
        The created `EntryCollection`.

    """
    if CONFIG.database_backend in (
        SupportedBackend.MONGODB,
        SupportedBackend.MONGOMOCK,
    ):
        from optimade.server.entry_collections.mongo import MongoCollection

        return MongoCollection(
            name=name,
            resource_cls=resource_cls,
            resource_mapper=resource_mapper,
        )

    if CONFIG.database_backend is SupportedBackend.ELASTIC:
        from optimade.server.entry_collections.elasticsearch import ElasticCollection

        return ElasticCollection(
            name=name,
            resource_cls=resource_cls,
            resource_mapper=resource_mapper,
        )

    raise NotImplementedError(
        f"The database backend {CONFIG.database_backend!r} is not implemented"
    )


class PaginationMechanism(enum.Enum):
    """The supported pagination mechanisms."""

    OFFSET = "page_offset"
    NUMBER = "page_number"
    CURSOR = "page_cursor"
    ABOVE = "page_above"
    BELOW = "page_below"


class EntryCollection(ABC):
    """Backend-agnostic base class for querying collections of
    [`EntryResource`][optimade.models.entries.EntryResource]s."""

    pagination_mechanism = PaginationMechanism("page_offset")
    """The default pagination mechansim to use with a given collection,
    if the user does not provide any pagination query parameters.
    """

    def __init__(
        self,
        resource_cls: type[EntryResource],
        resource_mapper: type[BaseResourceMapper],
        transformer: Transformer,
    ):
        """Initialize the collection for the given parameters.

        Parameters:
            resource_cls (EntryResource): The `EntryResource` model
                that is stored by the collection.
            resource_mapper (BaseResourceMapper): A resource mapper
                object that handles aliases and format changes between
                deserialization and response.
            transformer (Transformer): The Lark `Transformer` used to
                interpret the filter.

        """
        self.parser = LarkParser()
        self.resource_cls = resource_cls
        self.resource_mapper = resource_mapper
        self.transformer = transformer

        self.provider_prefix = CONFIG.provider.prefix
        self.provider_fields = [
            field if isinstance(field, str) else field["name"]
            for field in CONFIG.provider_fields.get(resource_mapper.ENDPOINT, [])
        ]

        self._all_fields: set[str] = set()

    @abstractmethod
    def __len__(self) -> int:
        """Returns the total number of entries in the collection."""

    @abstractmethod
    def insert(self, data: list[EntryResource]) -> None:
        """Add the given entries to the underlying database.

        Arguments:
            data: The entry resource objects to add to the database.

        """

    @abstractmethod
    def count(self, **kwargs: Any) -> Optional[int]:
        """Returns the number of entries matching the query specified
        by the keyword arguments.

        Parameters:
            **kwargs: Query parameters as keyword arguments.

        """

    def find(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> tuple[
        Optional[Union[dict[str, Any], list[dict[str, Any]]]],
        Optional[int],
        bool,
        set[str],
        set[str],
    ]:
        """
        Fetches results and indicates if more data is available.

        Also gives the total number of data available in the absence of `page_limit`.
        See [`EntryListingQueryParams`][optimade.server.query_params.EntryListingQueryParams]
        for more information.

        Returns a list of the mapped database reponse.

        If no results match the query, then `results` is set to `None`.

        Parameters:
            params: Entry listing URL query params.

        Returns:
            A tuple of various relevant values:
            (`results`, `data_returned`, `more_data_available`, `exclude_fields`, `include_fields`).

        """
        criteria = self.handle_query_params(params)
        single_entry = isinstance(params, SingleEntryQueryParams)
        response_fields: set[str] = criteria.pop("fields")

        raw_results, data_returned, more_data_available = self._run_db_query(
            criteria, single_entry
        )

        exclude_fields = self.all_fields - response_fields
        include_fields = (
            response_fields - self.resource_mapper.TOP_LEVEL_NON_ATTRIBUTES_FIELDS
        )

        bad_optimade_fields: set[str] = set()
        bad_provider_fields: set[str] = set()
        supported_prefixes = self.resource_mapper.SUPPORTED_PREFIXES
        all_attributes: set[str] = self.resource_mapper.ALL_ATTRIBUTES
        for field in include_fields:
            if field not in all_attributes:
                if field.startswith("_"):
                    if any(
                        field.startswith(f"_{prefix}_") for prefix in supported_prefixes
                    ):
                        bad_provider_fields.add(field)
                else:
                    bad_optimade_fields.add(field)

        if bad_provider_fields:
            warnings.warn(
                message=f"Unrecognised field(s) for this provider requested in `response_fields`: {bad_provider_fields}.",
                category=UnknownProviderProperty,
            )

        if bad_optimade_fields:
            raise BadRequest(
                detail=f"Unrecognised OPTIMADE field(s) in requested `response_fields`: {bad_optimade_fields}."
            )

        results: Optional[Union[list[dict[str, Any]], dict[str, Any]]] = None

        if raw_results:
            results = [self.resource_mapper.map_back(doc) for doc in raw_results]

            if single_entry:
                results = results[0]

                if (
                    CONFIG.validate_api_response
                    and data_returned is not None
                    and data_returned > 1
                ):
                    raise NotFound(
                        detail=f"Instead of a single entry, {data_returned} entries were found",
                    )
                else:
                    data_returned = 1

        return (
            results,
            data_returned,
            more_data_available,
            exclude_fields,
            include_fields,
        )

    @abstractmethod
    def _run_db_query(
        self, criteria: dict[str, Any], single_entry: bool = False
    ) -> tuple[list[dict[str, Any]], Optional[int], bool]:
        """Run the query on the backend and collect the results.

        Arguments:
            criteria: A dictionary representation of the query parameters.
            single_entry: Whether or not the caller is expecting a single entry response.

        Returns:
            The list of entries from the database (without any re-mapping), the total number of
            entries matching the query and a boolean for whether or not there is more data available.

        """

    @property
    def all_fields(self) -> set[str]:
        """Get the set of all fields handled in this collection,
        from attribute fields in the schema, provider fields and top-level OPTIMADE fields.

        The set of all fields are lazily created and then cached.
        This means the set is created the first time the property is requested and then cached.

        Returns:
            All fields handled in this collection.

        """
        if not self._all_fields:
            # All OPTIMADE fields
            self._all_fields = (
                self.resource_mapper.TOP_LEVEL_NON_ATTRIBUTES_FIELDS.copy()
            )
            self._all_fields |= self.get_attribute_fields()
            # All provider-specific fields
            self._all_fields |= {
                f"_{self.provider_prefix}_{field_name}"
                if not field_name.startswith("_")
                else field_name
                for field_name in self.provider_fields
            }

        return self._all_fields

    def get_attribute_fields(self) -> set[str]:
        """Get the set of attribute fields

        Return only the _first-level_ attribute fields from the schema of the resource class,
        resolving references along the way if needed.

        Note:
            It is not needed to take care of other special OpenAPI schema keys than `allOf`,
            since only `allOf` will be found in this context.
            Other special keys can be found in [the Swagger documentation](https://swagger.io/docs/specification/data-models/oneof-anyof-allof-not/).

        Returns:
            Property names.

        """
        annotation = _get_origin_type(
            self.resource_cls.model_fields["attributes"].annotation
        )

        if annotation in (None, NoneType) or not issubclass(annotation, Attributes):
            raise TypeError(
                "resource class 'attributes' field must be a subclass of 'EntryResourceAttributes'"
            )

        return set(annotation.model_fields)  # type: ignore[attr-defined]

    def handle_query_params(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> dict[str, Any]:
        """Parse and interpret the backend-agnostic query parameter models into a dictionary
        that can be used by the specific backend.

        Note:
            Currently this method returns the pymongo interpretation of the parameters,
            which will need modification for modified for other backends.

        Parameters:
            params: The initialized query parameter model from the server.

        Raises:
            Forbidden: If too large of a page limit is provided.
            BadRequest: If an invalid request is made, e.g., with incorrect fields
                or response format.

        Returns:
            A dictionary representation of the query parameters.

        """
        cursor_kwargs = {}

        # filter
        if getattr(params, "filter", False):
            cursor_kwargs["filter"] = self.transformer.transform(
                self.parser.parse(params.filter)  # type: ignore[union-attr]
            )
        else:
            cursor_kwargs["filter"] = {}

        # response_format
        if (
            getattr(params, "response_format", False)
            and params.response_format != "json"
        ):
            raise BadRequest(
                detail=f"Response format {params.response_format} is not supported, please use response_format='json'"
            )

        # page_limit
        if getattr(params, "page_limit", False):
            limit = params.page_limit  # type: ignore[union-attr]
            if limit > CONFIG.page_limit_max:
                raise Forbidden(
                    detail=f"Max allowed page_limit is {CONFIG.page_limit_max}, you requested {limit}",
                )
            cursor_kwargs["limit"] = limit
        else:
            cursor_kwargs["limit"] = CONFIG.page_limit

        # response_fields
        cursor_kwargs["projection"] = {
            f"{self.resource_mapper.get_backend_field(f)}": True
            for f in self.all_fields
        }

        if getattr(params, "response_fields", False):
            response_fields = set(params.response_fields.split(","))
            response_fields |= self.resource_mapper.get_required_fields()
        else:
            response_fields = self.all_fields.copy()

        cursor_kwargs["fields"] = response_fields

        # sort
        if getattr(params, "sort", False):
            cursor_kwargs["sort"] = self.parse_sort_params(params.sort)  # type: ignore[union-attr]

        # warn if multiple pagination keys are present, and only use the first from this list
        received_pagination_option = False
        warn_multiple_keys = False

        if getattr(params, "page_offset", False):
            received_pagination_option = True
            cursor_kwargs["skip"] = params.page_offset  # type: ignore[union-attr]

        if isinstance(getattr(params, "page_number", None), int):
            if received_pagination_option:
                warn_multiple_keys = True
            else:
                received_pagination_option = True
                if params.page_number < 1:  # type: ignore[union-attr]
                    warnings.warn(
                        message=f"'page_number' is 1-based, using 'page_number=1' instead of {params.page_number}",  # type: ignore[union-attr]
                        category=QueryParamNotUsed,
                    )
                    page_number = 1
                else:
                    page_number = params.page_number  # type: ignore[union-attr]
                cursor_kwargs["skip"] = (page_number - 1) * cursor_kwargs["limit"]

        if isinstance(getattr(params, "page_above", None), str):
            if received_pagination_option:
                warn_multiple_keys = True
            else:
                received_pagination_option = True
                cursor_kwargs["page_above"] = params.page_above  # type: ignore[union-attr]

        if warn_multiple_keys:
            warnings.warn(
                message="Multiple pagination keys were provided, only using the first one of 'page_offset', 'page_number' or 'page_above'",
                category=QueryParamNotUsed,
            )

        return cursor_kwargs

    def parse_sort_params(self, sort_params: str) -> Iterable[tuple[str, int]]:
        """Handles any sort parameters passed to the collection,
        resolving aliases and dealing with any invalid fields.

        Raises:
            BadRequest: if an invalid sort is requested.

        Returns:
            A list of tuples containing the aliased field name and
            sort direction encoded as 1 (ascending) or -1 (descending).

        """
        sort_spec: list[tuple[str, int]] = []
        for field in sort_params.split(","):
            sort_dir = 1
            if field.startswith("-"):
                field = field[1:]
                sort_dir = -1
            aliased_field = self.resource_mapper.get_backend_field(field)
            sort_spec.append((aliased_field, sort_dir))

        unknown_fields = [
            field
            for field, _ in sort_spec
            if self.resource_mapper.get_optimade_field(field) not in self.all_fields
        ]

        if unknown_fields:
            error_detail = "Unable to sort on unknown field{} '{}'".format(
                "s" if len(unknown_fields) > 1 else "",
                "', '".join(unknown_fields),
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
        sort_spec = [
            (field, sort_dir)
            for field, sort_dir in sort_spec
            if field not in unknown_fields
        ]

        return sort_spec

    def get_next_query_params(
        self,
        params: EntryListingQueryParams,
        results: Optional[Union[dict[str, Any], list[dict[str, Any]]]],
    ) -> dict[str, list[str]]:
        """Provides url query pagination parameters that will be used in the next
        link.

        Arguments:
            results: The results produced by find.
            params: The parsed request params produced by handle_query_params.

        Returns:
            A dictionary with the necessary query parameters.

        """
        query: dict[str, list[str]] = dict()
        if isinstance(results, list) and results:
            # If a user passed a particular pagination mechanism, keep using it
            # Otherwise, use the default pagination mechanism of the collection
            pagination_mechanism = PaginationMechanism.OFFSET
            for pagination_key in (
                "page_offset",
                "page_number",
                "page_above",
            ):
                if getattr(params, pagination_key, None) is not None:
                    pagination_mechanism = PaginationMechanism(pagination_key)
                    break

            if pagination_mechanism == PaginationMechanism.OFFSET:
                query["page_offset"] = [
                    str(params.page_offset + len(results))  # type: ignore[list-item]
                ]

        return query
