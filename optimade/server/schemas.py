from typing import Dict, Callable
from optimade.models import (
    DataType,
    ErrorResponse,
    StructureResource,
    ReferenceResource,
)
from optimade.server.exceptions import POSSIBLE_ERRORS

__all__ = ("ENTRY_INFO_SCHEMAS", "ERROR_RESPONSES", "retrieve_queryable_properties")

ENTRY_INFO_SCHEMAS: Dict[str, Callable[[None], Dict]] = {
    "structures": StructureResource.schema,
    "references": ReferenceResource.schema,
}
"""This dictionary is used to define the `/info/<entry_type>` endpoints."""

ERROR_RESPONSES: Dict[int, Dict] = {
    err.status_code: {"model": ErrorResponse, "description": err.title}
    for err in POSSIBLE_ERRORS
}


def retrieve_queryable_properties(
    schema: dict,
    queryable_properties: list = None,
    entry_type: str = None,
) -> dict:
    """Recursively loops through the schema of a pydantic model and
    resolves all references, returning a dictionary of all the
    OPTIMADE-queryable properties of that model.

    Parameters:
        schema: The schema of the pydantic model.
        queryable_properties: The list of properties to find in the schema.
        entry_type: An optional entry type for the model. Will be used to
            lookup schemas for any config-defined fields.

    Returns:
        A flat dictionary with properties as keys, containing the field
        description, unit, sortability, support level, queryability
        and type, where provided.

    """
    properties = {}
    for name, value in schema["properties"].items():
        if not queryable_properties or name in queryable_properties:
            if "$ref" in value:
                path = value["$ref"].split("/")[1:]
                sub_schema = schema.copy()
                while path:
                    next_key = path.pop(0)
                    sub_schema = sub_schema[next_key]
                sub_queryable_properties = sub_schema["properties"].keys()
                properties.update(
                    retrieve_queryable_properties(sub_schema, sub_queryable_properties)
                )
            else:
                properties[name] = {"description": value.get("description", "")}
                # Update schema with extension keys provided they are not None
                for key in [_ for _ in ("unit", "queryable", "support") if _ in value]:
                    properties[name][key] = value[key]
                # All properties are sortable with the MongoDB backend.
                # While the result for sorting lists may not be as expected, they are still sorted.
                properties[name]["sortable"] = value.get("sortable", True)
                # Try to get OpenAPI-specific "format" if possible, else get "type"; a mandatory OpenAPI key.
                properties[name]["type"] = DataType.from_json_type(
                    value.get("format", value.get("type"))
                )

    # If specified, check the config for any additional well-described provider fields
    if entry_type:
        from optimade.server.config import CONFIG

        described_provider_fields = [
            field
            for field in CONFIG.provider_fields.get(entry_type, {})
            if isinstance(field, dict)
        ]
        for field in described_provider_fields:
            name = f"_{CONFIG.provider.prefix}_{field['name']}"
            properties[name] = {k: field[k] for k in field if k != "name"}
            properties[name]["sortable"] = field.get("sortable", True)

    return properties
