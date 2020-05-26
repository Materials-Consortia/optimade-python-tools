from optimade.models import (
    StructureResource,
    ReferenceResource,
    LinksResource,
    EntryResource,
    DataType
)
from .config import CONFIG


def retrieve_queryable_properties(
    schema: dict, queryable_properties: list, entry_provider_fields: list = None
) -> dict:
    """ For a given schema dictionary and a list of desired properties,
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
                    value.get("format", value["type"])
                )

            if name in entry_provider_fields:
                # Rename fields in schema according to provider field list
                properties[f"_{CONFIG.provider.prefix}_{name}"] = properties.pop(name)

    return properties


class EntrySchemas:
    """ Wrapper class for EntryResource schemas used in this server. Any
    references in the schema are resolved to allow for easy use. If the
    underyling model is updated, the schema will be refreshed.

    """

    def __init__(self):
        self._structure_model = StructureResource
        self._reference_model = ReferenceResource
        self._links_model = LinksResource
        self._structures = None
        self._references = None
        self._links = None

    def keys(self):
        return {"structures", "references", "links"}

    def get(self, key: str):
        return getattr(self, key, {})

    @property
    def structures(self):
        if self._structures is None:
            schema = self.structure_model.schema()
            entry_provider_fields = CONFIG.provider_fields.get("structures")
            self._structures = retrieve_queryable_properties(
                schema,
                schema["properties"].keys(),
                entry_provider_fields=entry_provider_fields,
            )

        return self._structures

    @property
    def references(self):
        if self._references is None:
            schema = self.reference_model.schema()
            entry_provider_fields = CONFIG.provider_fields.get("references")
            self._references = retrieve_queryable_properties(
                schema,
                schema["properties"].keys(),
                entry_provider_fields=entry_provider_fields,
            )

        return self._references

    @property
    def links(self):
        if self._links is None:
            # links should not permit provider-specific fields
            schema = self.links_model.schema()
            self._links = retrieve_queryable_properties(
                schema, schema["properties"].keys(), entry_provider_fields=None
            )
        return self._links

    @property
    def structure_model(self):
        return self._structure_model

    @structure_model.setter
    def structure_model(self, model: EntryResource):
        self._structures = None
        self._structure_model = model

    @property
    def reference_model(self):
        return self._reference_model

    @reference_model.setter
    def reference_model(self, model: EntryResource):
        self._references = None
        self._reference_model = model

    @property
    def links_model(self):
        return self._links_model

    @links_model.setter
    def links_model(self, model: EntryResource):
        self._links = None
        self._links_model = model


ENTRY_SCHEMAS = EntrySchemas()
