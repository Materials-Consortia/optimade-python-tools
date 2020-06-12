# pylint: disable=relative-beyond-top-level,import-outside-toplevel
import unittest

from pydantic import Field
from optimade.server.schemas import ENTRY_SCHEMAS, retrieve_queryable_properties
from optimade.models import (
    StructureResource,
    StructureResourceAttributes,
    ReferenceResource,
    EntryResource,
)


class SchemaTests(unittest.TestCase):
    """ Test the dynamic setting/loading of EntrySchemas from the specified models. """

    def test_default_schemas(self):
        def _test_default_schema(resource: EntryResource, endpoint_name: str):

            resource_schema = resource.schema()

            resource_schema = retrieve_queryable_properties(
                resource_schema,
                resource_schema["properties"].keys(),
                entry_provider_fields=[],
            )

            # test key access
            entry_schema = ENTRY_SCHEMAS[endpoint_name]
            self.assertDictEqual(entry_schema, resource_schema)

            # test getattr access
            entry_schema = getattr(ENTRY_SCHEMAS, endpoint_name)
            self.assertDictEqual(entry_schema, resource_schema)

        endpoints = [
            (StructureResource, "structures"),
            (ReferenceResource, "references"),
        ]
        for resource, endpoint_name in endpoints:

            self.assertTrue(endpoint_name in ENTRY_SCHEMAS)
            _test_default_schema(resource, endpoint_name)

    def test_modified_schema(self):
        class MyStructureResourceAttributes(StructureResourceAttributes):
            extra_field: float = Field(..., description="My extra field.")

        class MyStructureResource(StructureResource):
            attributes: MyStructureResourceAttributes

        ENTRY_SCHEMAS["structures"] = MyStructureResource

        my_structure_schema = ENTRY_SCHEMAS["structures"]
        self.assertTrue("extra_field" in my_structure_schema)

    def test_nonexistent_schema(self):
        with self.assertRaises(AttributeError):
            ENTRY_SCHEMAS["not_an_endpoint_name"]
