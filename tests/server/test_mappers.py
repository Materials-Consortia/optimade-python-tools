# pylint: disable=relative-beyond-top-level,import-outside-toplevel
import unittest
import mongomock

from optimade.server.mappers import BaseResourceMapper
from optimade.server.entry_collections import MongoCollection
from optimade.models import StructureResource


class ResourceMapperTests(unittest.TestCase):
    def test_disallowed_aliases(self):
        class MyMapper(BaseResourceMapper):
            ALIASES = (("$and", "my_special_and"), ("not", "$not"))

        mapper = MyMapper()
        toy_collection = mongomock.MongoClient()["fake"]["fake"]
        with self.assertRaises(RuntimeError):
            MongoCollection(toy_collection, StructureResource, mapper)

    def test_property_aliases(self):
        class MyMapper(BaseResourceMapper):
            PROVIDER_FIELDS = ("dft_parameters", "test_field")
            LENGTH_ALIASES = (("_exmpl_test_field", "test_field_len"),)
            ALIASES = (("field", "completely_different_field"),)

        mapper = MyMapper()
        self.assertEqual(mapper.alias_for("_exmpl_dft_parameters"), "dft_parameters")
        self.assertEqual(mapper.alias_for("_exmpl_test_field"), "test_field")
        self.assertEqual(mapper.alias_for("field"), "completely_different_field")
        self.assertEqual(mapper.length_alias_for("_exmpl_test_field"), "test_field_len")
        self.assertEqual(mapper.length_alias_for("test_field"), None)
        self.assertEqual(mapper.alias_for("test_field"), "test_field")

        # nested properties
        self.assertEqual(
            mapper.alias_for("_exmpl_dft_parameters.nested.property"),
            "dft_parameters.nested.property",
        )
        self.assertEqual(
            mapper.alias_for("_exmpl_dft_parameters.nested_property"),
            "dft_parameters.nested_property",
        )

        # test nonsensical query
        self.assertEqual(mapper.alias_for("_exmpl_test_field."), "test_field.")

        # test an awkward case that has no alias
        self.assertEqual(
            mapper.alias_for("_exmpl_dft_parameters_dft_parameters.nested.property"),
            "_exmpl_dft_parameters_dft_parameters.nested.property",
        )
