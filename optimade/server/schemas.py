from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, TypeAdapter

from optimade.models import (
    DataType,
    EntryResource,
    ErrorResponse,
    ReferenceResource,
    StructureResource,
)
from optimade.models.types import NoneType, _get_origin_type

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

__all__ = ("ENTRY_INFO_SCHEMAS", "ERROR_RESPONSES", "retrieve_queryable_properties")

ENTRY_INFO_SCHEMAS: dict[str, type[EntryResource]] = {
    "structures": StructureResource,
    "references": ReferenceResource,
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

    ERROR_RESPONSES: Optional[dict[int, dict[str, Any]]] = {
        err.status_code: {"model": ErrorResponse, "description": err.title}
        for err in POSSIBLE_ERRORS
    }
except ModuleNotFoundError:
    ERROR_RESPONSES = None


def retrieve_queryable_properties(
    schema: type[EntryResource],
    queryable_properties: Optional[Iterable[str]] = None,
    entry_type: Optional[str] = None,
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
    if entry_type:
        from optimade.server.config import CONFIG

        described_provider_fields = [
            field
            for field in CONFIG.provider_fields.get(entry_type, {})  # type: ignore[call-overload]
            if isinstance(field, dict)
        ]
        for field in described_provider_fields:
            name = (
                f"_{CONFIG.provider.prefix}_{field['name']}"
                if not field["name"].startswith("_")
                else field["name"]
            )
            properties[name] = {k: field[k] for k in field if k != "name"}
            properties[name]["sortable"] = field.get("sortable", True)

    # Remove JSON fields mistaken as properties
    non_property_fields = ["attributes", "relationships"]
    for non_property_field in non_property_fields:
        if non_property_field in properties:
            del properties[non_property_field]

    return properties
