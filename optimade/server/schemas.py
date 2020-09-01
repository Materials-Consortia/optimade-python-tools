from optimade import models
from optimade.server.config import CONFIG
from typing import Dict, Union, Any


def retrieve_queryable_properties(
    schema: dict,
    queryable_properties: list,
    entry_provider_fields: list = None,
    base_schema: dict = None,
) -> dict:
    """Retrieve schema properties.

    For a given schema dictionary and a list of desired properties,
    recursively descend into the schema and set the appropriate values
    for the `description`, `sortable` and `unit` keys, returning the expanded
    schema dict that includes nested schemas.

    """
    properties = {}
    if entry_provider_fields is None:
        entry_provider_fields = []

    if base_schema is None:
        base_schema = schema.copy()

    for name, value in schema["properties"].items():
        if name in queryable_properties:
            _keys = ("allOf", "anyOf", "oneOf")
            for key in _keys:
                if key in value:
                    condOf = value.pop(key)
                    if isinstance(condOf, list):
                        # ml-evs: A bit of late-night hack; we need to think more about how to
                        # unwrap the case where multiple types are allowed for a given field.
                        # Here I just grab the first, for the sake of testing.
                        value.update(condOf[0])

            if "$ref" in value:
                path = value["$ref"].split("/")[1:]
                sub_schema = base_schema.copy()
                while path:
                    next_key = path.pop(0)
                    sub_schema = sub_schema[next_key]
                sub_queryable_properties = sub_schema["properties"].keys()
                properties.update(
                    retrieve_queryable_properties(
                        sub_schema,
                        sub_queryable_properties,
                        entry_provider_fields,
                        base_schema=base_schema,
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
                properties[name]["type"] = models.DataType.from_json_type(
                    value.get("format", value["type"])
                )

            if name in entry_provider_fields:
                # Rename fields in schema according to provider field list
                properties[f"_{CONFIG.provider.prefix}_{name}"] = properties.pop(name)

    return properties


class Schema:
    """
    Wrapper for output of pydantic model's `schema()` method.

    The passed schema output can be retrieved from the `schema` property.
    Mostly, this will be used to retrieve a de-referenced dictionary of the properties
    of a model's schema. This can be done by retrieving the `properties` property.

    It will recursively try to de-reference the properties by finding all instances of `$ref`
    and either exchanging it with a "base" definition, i.e., a definition of the reference
    without any references itself. Or it will try to find the reference in the specified
    local reference location in the schema. And finally, if this does not find it, the class
    will try to import the referenced model from `optimade.models` and return _that_ imported
    model's `schema()` output.

    Arguments:
        schema (dict): The output of a pydantic model's `schema()` method.

    """

    def __init__(self, schema: dict) -> None:
        self._schema = schema

        self._properties = None
        self._base_definitions = {
            _: value
            for _, value in self._schema["definitions"].items()
            if not self._contains_reference(value)
        }

    @property
    def schema(self) -> dict:
        """The raw JSON Schema as a Python dictionary."""
        return self._schema

    @schema.setter
    def schema(self, value: dict) -> None:
        """Set a new JSON Schema.

        Note, this will re-initialize the object instance, perhaps losing already set `properties` attribute.
        """
        if not isinstance(value, dict):
            raise TypeError(f"schema must be a dict, you passed a {type(value)}")
        self.__init__(value)  # Re-initalizing

    @property
    def properties(self) -> dict:
        """The schema's properties in a de-referenced dictionary.

        By de-referenced it is meant that all `$ref` entries will be replaced with actual definitions.
        """
        if self._properties is None:
            self._properties = self._dereference_recursively(
                self.schema["properties"].copy()
            )

        return self._properties

    def _contains_reference(self, schema: dict) -> str:
        """Determine whether a JSON Schema object contains a reference (`$ref` key).

        Parameters:
            schema: A JSON Schema object.

        Returns:
            The first found reference value, i.e., a `$ref` key's value.

        """
        for key, value in schema.items():
            if key == "$ref":
                return value
            if isinstance(value, dict):
                res = self._contains_reference(value)
                if res:
                    return res
            elif isinstance(value, (tuple, list)):
                for item in value:
                    if isinstance(item, dict):
                        res = self._contains_reference(item)
                        if res:
                            return res
        return ""

    def _get_py_model_schema(self, model_name: str) -> dict:
        """Retrieve the schema from a Python pydantic model in `optimade.models`.

        Parameters:
            model_name: The name of the model to be imported from `optimade.models`.

        Returns:
            The output of the pydantic model's `schema()` method.

        """
        try:
            model = getattr(models, model_name)
        except AttributeError:
            return {}
        else:
            return model.schema()

    def _get_ref(self, reference: str) -> dict:
        """Retrieve a JSON Schema object reference.

        Parameters:
            reference: JSON Schema `$ref` value, e.g., `"#/componenets/schemas/User"`.

        Returns:
            The referenced JSON Schema object.

        """
        if not reference.startswith("#"):
            raise NotImplementedError(
                "Only local JSON references can be handled by Schema."
            )

        name = reference.split("/")[-1]
        if name in self._base_definitions:
            return self._base_definitions[name]

        path = reference[len("#/") :].split("/")
        sub_schema = {}
        while path:
            name = path.pop(0)
            sub_schema = sub_schema.get(
                name, self.schema.get(name, self._get_py_model_schema(name))
            )

        sub_reference = self._contains_reference(sub_schema)
        if sub_reference:
            while sub_reference:
                sub_schema = self._dereference_recursively(sub_schema)
                sub_reference = self._contains_reference(sub_schema)
        else:
            # Update self._base_definitions
            self._base_definitions.update({name: sub_schema})

        return sub_schema

    def _dereference_recursively(self, schema: Any) -> Any:
        """De-reference a schema (part) recursively.

        Since a reference will _always_ be a single `dict` with key `"$ref"`,
        this can be exploited to return the reference target whenever `schema`
        is a `dict` with key `"$ref"`.
        Otherwise we return the schema right back, making sure to enter into all
        containers of any kind.
        """
        if isinstance(schema, dict):
            if "$ref" in schema:
                return self._get_ref(schema["$ref"])
            return {
                _: self._dereference_recursively(value) for _, value in schema.items()
            }
        elif isinstance(schema, (tuple, set, list)):
            return type(schema)([self._dereference_recursively(_) for _ in schema])
        else:
            return schema


class EntrySchemas:
    """
    Wrapper class for EntryResource schemas used in this server.

    Any references in the schema are resolved to allow for easy use.
    If the underlying model is updated, the schema will be refreshed.

    """

    def __init__(self):
        self._entry_models: Dict[str, models.EntryResource] = {
            "structures": models.StructureResource,
            "references": models.ReferenceResource,
        }
        self._entry_schemas: Dict[str, Union[None, dict]] = {}
        self._entry_properties: Dict[str, models.EntryInfoProperty] = {}

    def keys(self):
        return self._entry_models.keys()

    def get(self, entry_type, default=None):
        return getattr(self, entry_type, default)

    def __contains__(self, entry_type):
        return entry_type in self.keys()

    def __getitem__(self, entry_type: str):
        try:
            return getattr(self, entry_type)
        except AttributeError as exc:
            raise KeyError(str(exc))

    def __setitem__(self, entry_type: str, entry_model: models.EntryResource):
        if entry_type in self._entry_models:
            self._entry_models[entry_type] = entry_model
            self._entry_schemas[entry_type] = None
        else:
            raise KeyError(
                f"Can only set existing keys. {entry_type!r} is not recognized as an existing key."
            )

    def __getattr__(self, entry_type, default=None):
        if entry_type not in self._entry_models:
            raise AttributeError(f"Requested entry type {entry_type!r} has no model.")
        return self._get_expanded_entry_schema(entry_type)

    def _get_expanded_entry_schema(self, entry_type):
        if self._entry_schemas.get(entry_type) is None:
            model = self._entry_models.get(entry_type)
            if model is None:
                raise AttributeError(
                    f"Missing model for {entry_type!r} in EntrySchemas."
                )
            self._entry_schemas[entry_type] = model.schema()
            self._entry_properties[entry_type] = self._entry_schemas[entry_type].get(
                "properties", {}
            )

            entry_provider_fields = CONFIG.provider_fields.get(entry_type)
            self._entry_properties[entry_type] = retrieve_queryable_properties(
                self._entry_schemas[entry_type],
                self._entry_properties.keys(),
                entry_provider_fields=entry_provider_fields,
            )

        return self._entry_schemas[entry_type]


ENTRY_SCHEMAS = EntrySchemas()
