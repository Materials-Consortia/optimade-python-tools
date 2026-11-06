from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, TypeAdapter

from optimade.models import (
    DataType,
    EntryResource,
    ErrorResponse,
    FileResource,
    ReferenceResource,
    StructureResource,
)
from optimade.models.property_definitions import (
    complete_property_definition,
    get_meta_schema_url,
    get_standard_entry_type_definition,
    property_definition_from_description,
    property_definition_from_json_schema,
)
from optimade.models.types import NoneType, _get_origin_type
from optimade.server.config import ServerConfig
from optimade.server.logger import get_logger

if TYPE_CHECKING:  # pragma: no cover
    from typing import Literal, Union

    from optimade.models.utils import SupportLevel

    QueryableProperties = dict[
        str,
        dict[
            Literal["description", "unit", "queryable", "support", "sortable", "type"],
            Optional[Union[str, SupportLevel, bool, DataType]],
        ],
    ]

__all__ = (
    "ENTRY_INFO_SCHEMAS",
    "ERROR_RESPONSES",
    "retrieve_queryable_properties",
    "retrieve_property_definitions",
    "get_provider_field_definition",
)

ENTRY_INFO_SCHEMAS: dict[str, type[EntryResource]] = {
    "structures": StructureResource,
    "references": ReferenceResource,
    "files": FileResource,
}
"""This dictionary is used to define the `/info/<entry_type>` endpoints."""

try:
    """The possible errors list contains FastAPI/starlette exception objects
    This dictionary is only used for constructing the OpenAPI schema, i.e.,
    a development task, so can be safely nulled to allow other non-server
    submodules (e.g., the validator) to access the other schemas
    (that only require pydantic to construct).
    """
    from optimade.exceptions import POSSIBLE_ERRORS

    ERROR_RESPONSES: dict[int, dict[str, Any]] | None = {
        err.status_code: {"model": ErrorResponse, "description": err.title}
        for err in POSSIBLE_ERRORS
    }
except ModuleNotFoundError:
    ERROR_RESPONSES = None


def retrieve_queryable_properties(
    schema: type[EntryResource],
    queryable_properties: Iterable[str] | None = None,
    entry_type: str | None = None,
    config: ServerConfig | None = None,
) -> "QueryableProperties":
    """Recursively loops through a pydantic model, returning a dictionary of all the
    OPTIMADE-queryable properties of that model.

    Parameters:
        schema: The pydantic model.
        queryable_properties: The list of properties to find in the schema.
        entry_type: An optional entry type for the model. Will be used to
            lookup schemas for any config-defined fields.

    Returns:
        A flat dictionary with properties as keys, containing the field
        description, unit, sortability, support level, queryability
        and type, where provided.

    """
    properties: "QueryableProperties" = {}
    for name, value in schema.model_fields.items():
        # Proceed if the field (name) is given explicitly in the queryable_properties
        # list or if the queryable_properties list is empty (i.e., all properties are
        # requested)
        if not queryable_properties or name in queryable_properties:
            if name in properties:
                continue

            # If the field is another data model, "unpack" it by recursively calling
            # this function.
            # But first, we need to "unpack" the annotation, getting in behind any
            # Optional, Union, or Annotated types.
            annotation = _get_origin_type(value.annotation)

            if annotation not in (None, NoneType) and issubclass(annotation, BaseModel):
                sub_queryable_properties = list(annotation.model_fields)  # type: ignore[attr-defined]
                properties.update(
                    retrieve_queryable_properties(annotation, sub_queryable_properties)
                )

            properties[name] = {"description": value.description or ""}

            # Update schema with extension keys, provided they are not None
            for key in (
                "x-optimade-unit",
                "x-optimade-queryable",
                "x-optimade-support",
            ):
                if (
                    value.json_schema_extra
                    and value.json_schema_extra.get(key) is not None
                ):
                    properties[name][
                        key.replace("x-optimade-", "")  # type: ignore[index]
                    ] = value.json_schema_extra[key]

            # All properties are sortable with the MongoDB backend.
            # While the result for sorting lists may not be as expected, they are still sorted.
            properties[name]["sortable"] = (
                value.json_schema_extra.get("x-optimade-sortable", True)
                if value.json_schema_extra
                else True
            )

            # Try to get OpenAPI-specific "format" if possible, else get "type"; a mandatory OpenAPI key.
            json_schema = TypeAdapter(annotation).json_schema(mode="validation")

            properties[name]["type"] = DataType.from_json_type(
                json_schema.get("format", json_schema.get("type"))
            )

    # If specified, check the config for any additional well-described provider fields
    if entry_type and config:
        described_provider_fields = [
            field
            for field in config.provider_fields.get(entry_type, {})  # type: ignore[call-overload]
            if isinstance(field, dict)
        ]
        for field in described_provider_fields:
            name = (
                f"_{config.provider.prefix}_{field['name']}"
                if not field["name"].startswith("_")
                else field["name"]
            )
            if field.get("definition") is not None:
                # Extract the pre-v1.2 description from a full property definition
                definition = field["definition"]
                properties[name] = {"description": definition.get("description", "")}
                if definition.get("x-optimade-type") in DataType.get_values():
                    properties[name]["type"] = definition["x-optimade-type"]
                if definition.get("x-optimade-unit") not in (
                    None,
                    "dimensionless",
                    "inapplicable",
                ):
                    properties[name]["unit"] = definition["x-optimade-unit"]
            else:
                properties[name] = {k: field[k] for k in field if k != "name"}
            properties[name]["sortable"] = field.get("sortable", True)

    # Remove JSON fields mistaken as properties
    non_property_fields = ["attributes", "relationships"]
    for non_property_field in non_property_fields:
        if non_property_field in properties:
            del properties[non_property_field]

    return properties


_UNDEFINED_PROPERTIES: set[tuple[str | None, str]] = set()
"""The properties that have already been reported as lacking a definition."""


def _warn_undefined_property(entry_type: str | None, name: str, reason: str) -> None:
    """Logs, once per property, that no definition could be created for it."""
    if (entry_type, name) in _UNDEFINED_PROPERTIES:
        return
    _UNDEFINED_PROPERTIES.add((entry_type, name))
    get_logger().warning(
        "Property %r will not be listed at `/info/%s` as no property definition could be "
        "created for it: %s Consider providing a full definition for it instead.",
        name,
        entry_type,
        reason,
    )


def _find_model_field(schema: type[EntryResource], name: str) -> Any:
    """Returns the pydantic field for the given top-level field or attribute."""
    if name in schema.model_fields:
        return schema.model_fields[name]

    attributes = schema.model_fields.get("attributes")
    if attributes is not None:
        annotation = _get_origin_type(attributes.annotation)
        if annotation not in (None, NoneType) and issubclass(annotation, BaseModel):
            return annotation.model_fields.get(name)  # type: ignore[attr-defined]

    return None


def get_provider_field_definition(
    field: dict[str, Any], entry_type: str, config: ServerConfig
) -> tuple[str, dict[str, Any]]:
    """Creates the property definition for a provider field that has been
    described under the `provider_fields` configuration option, either with
    a full `definition`, or with the `description`, `type` and `unit` keys.

    Parameters:
        field: The entry of `provider_fields` describing the field.
        entry_type: The entry type that the field belongs to.
        config: The server configuration.

    Raises:
        ValueError: If there is not enough information to create a definition.
        pydantic.ValidationError: If the configured definition is not valid.

    Returns:
        The prefixed name of the field, and its property definition.

    """
    name = (
        f"_{config.provider.prefix}_{field['name']}"
        if not field["name"].startswith("_")
        else field["name"]
    )

    if field.get("definition") is not None:
        definition = complete_property_definition(field["definition"], name, entry_type)
    else:
        definition = property_definition_from_description(field, name, entry_type)

    # All properties are sortable with the MongoDB backend, unless stated otherwise
    definition["x-optimade-implementation"] = {
        "sortable": field.get("sortable", True),
        **definition.get("x-optimade-implementation", {}),
    }

    return name, definition


def retrieve_property_definitions(
    schema: type[EntryResource],
    entry_type: str,
    config: ServerConfig | None = None,
) -> dict[str, dict[str, Any]]:
    """Returns the OPTIMADE Property Definitions for all of the properties served
    for the given entry type, in the format introduced in v1.2 of the specification.

    Definitions are taken, in order of preference, from:

    1. the standard definitions published for the supported version of the
       specification at `https://schemas.optimade.org/defs`, such that the `$id` of
       each property resolves to its canonical definition,
    2. the pydantic model for the entry type, for any fields that are not part
       of the specification,
    3. the `provider_fields` configuration option.

    The functionality provided by this implementation is then described under
    `x-optimade-implementation`.

    Parameters:
        schema: The pydantic model for the entry type.
        entry_type: The entry type, e.g., `"structures"`.
        config: The server configuration, used to look up any provider fields.

    Returns:
        A dictionary with property names as keys and property definitions as values.

    """
    model_properties = retrieve_queryable_properties(
        schema, {"id", "type", "attributes"}
    )
    standard_definitions = (get_standard_entry_type_definition(entry_type) or {}).get(
        "properties", {}
    )

    definitions: dict[str, dict[str, Any]] = {}
    for name, model_property in model_properties.items():
        if name in standard_definitions:
            definition = standard_definitions[name]
            definition.setdefault(
                "$schema",
                get_meta_schema_url(definition["x-optimade-definition"]["format"]),
            )
        else:
            field = _find_model_field(schema, name)
            if field is None:
                continue
            try:
                definition = property_definition_from_json_schema(
                    {
                        "description": field.description,
                        **TypeAdapter(field.annotation).json_schema(mode="validation"),
                    },
                    name,
                    entry_type,
                    unit=field.json_schema_extra.get("x-optimade-unit")
                    if isinstance(field.json_schema_extra, dict)
                    else None,
                )
            except ValueError as exc:
                _warn_undefined_property(entry_type, name, str(exc))
                continue

        implementation = {"sortable": bool(model_property.get("sortable", True))}

        # The reference server is tested against the level of query support
        # required by the specification, so only this level is advertised.
        query_support = definition.get("x-optimade-requirements", {}).get(
            "query-support"
        )
        if query_support and query_support != "partial":
            implementation["query-support"] = query_support

        definition["x-optimade-implementation"] = implementation
        definitions[name] = definition

    if config:
        for provider_field in config.provider_fields.get(entry_type, []):  # type: ignore[call-overload]
            if not isinstance(provider_field, dict):
                continue
            try:
                name, definition = get_provider_field_definition(
                    provider_field, entry_type, config
                )
            except ValueError as exc:
                _warn_undefined_property(
                    entry_type, provider_field.get("name", ""), str(exc)
                )
                continue
            definitions[name] = definition

    return definitions
