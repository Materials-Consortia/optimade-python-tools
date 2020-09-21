from optimade.models import DataType, StructureResource, ReferenceResource

ENTRY_INFO_SCHEMAS = {
    "structures": StructureResource.schema,
    "references": ReferenceResource.schema,
}


def retrieve_queryable_properties(schema: dict, queryable_properties: list) -> dict:
    properties = {}
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
                    retrieve_queryable_properties(sub_schema, sub_queryable_properties)
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
    return properties
