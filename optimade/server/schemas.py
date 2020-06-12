from optimade.models import (
    StructureResource,
    ReferenceResource,
    EntryResource,
    DataType,
)
from .config import CONFIG
from typing import Dict, Union


def retrieve_queryable_properties(
    schema: dict, queryable_properties: list, entry_provider_fields: list = None
) -> dict:
    """For a given schema dictionary and a list of desired properties,
    recursively descend into the schema and set the appropriate values
    for the `description`, `sortable` and `unit` keys, returning the expanded
    schema dict that includes nested schemas.

    """
    properties = {}
    if entry_provider_fields is None:
        entry_provider_fields = []

    for name, value in schema["properties"].items():
        if name in queryable_properties:
            if "$ref" in value:
                path = value["$ref"].split("/")[1:]
                sub_schema = schema.copy()
                while path:
                    next_key = path.pop(0)
                    sub_schema = sub_schema[next_key]
                sub_queryable_properties = sub_schema["properties"].keys()
                properties.update(
                    retrieve_queryable_properties(
                        sub_schema, sub_queryable_properties, entry_provider_fields
                    )
                )
            else:
                properties[name] = {"description": value.get("description", "")}
                if "unit" in value:
                    properties[name]["unit"] = value["unit"]
                # All properties are sortable with the MongoDB backend.
                # While the result for sorting lists may not be as expected, they are still sorted.
                properties[name]["sortable"] = True
                # Try to get OpenAPI-specific "format" if possible, else get "type"; a mandatory OpenAPI key.
                properties[name]["type"] = DataType.from_json_type(
                    value.get("format", value.get("type", "object"))
                )

            if name in entry_provider_fields:
                # Rename fields in schema according to provider field list
                properties[f"_{CONFIG.provider.prefix}_{name}"] = properties.pop(name)

    return properties


class EntrySchemas:
    """Wrapper class for EntryResource schemas used in this server. Any
    references in the schema are resolved to allow for easy use. If the
    underyling model is updated, the schema will be refreshed.

    """

    def __init__(self):
        self._entry_models: Dict[str, EntryResource] = {
            "structures": StructureResource,
            "references": ReferenceResource,
        }
        self._entry_schemas: Dict[str, Union[None, dict]] = {}

    def keys(self):
        return self._entry_models.keys()

    def get(self, entry_type, default=None):
        return getattr(self, entry_type, default)

    def __contains__(self, entry_type):
        return entry_type in self.keys()

    def __getitem__(self, entry_type: str):
        return getattr(self, entry_type)

    def __setitem__(self, entry_type: str, entry_model: EntryResource):
        if entry_type in self._entry_models:
            self._entry_models[entry_type] = entry_model
            self._entry_schemas[entry_type] = None

    def __getattr__(self, entry_type, default=None):
        if entry_type not in self._entry_models:
            raise AttributeError(f"Requested entry type {entry_type} has no model.")
        return self._get_expanded_entry_schema(entry_type)

    def _get_expanded_entry_schema(self, entry_type):
        if self._entry_schemas.get(entry_type, None) is None:
            model = self._entry_models.get(entry_type, None)
            if model is None:
                raise AttributeError(f"Missing model for {entry_type} in EntrySchemas.")
            schema = model.schema()

            entry_provider_fields = CONFIG.provider_fields.get(entry_type)
            self._entry_schemas[entry_type] = retrieve_queryable_properties(
                schema,
                schema["properties"].keys(),
                entry_provider_fields=entry_provider_fields,
            )

        return self._entry_schemas[entry_type]


ENTRY_SCHEMAS = EntrySchemas()
