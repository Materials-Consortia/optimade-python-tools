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

    def test_allowed_aliases(self):
        class MyStructureMapper(BaseResourceMapper):
            ALIASES = (
                ("elements", "my_elements"),
                ("A", "D"),
                ("B", "E"),
                ("C", "F"),
            )

        mapper = MyStructureMapper()
        self.assertEqual(mapper.alias_for("elements"), "my_elements")

        toy_collection = mongomock.MongoClient()["fake"]["fake"]
        collection = MongoCollection(toy_collection, StructureResource, mapper)

        test_filter = {"elements": {"$in": ["A", "B", "C"]}}
        self.assertEqual(
            collection._alias_filter(test_filter),
            {"my_elements": {"$in": ["A", "B", "C"]}},
        )
        test_filter = {"$and": [{"elements": {"$in": ["A", "B", "C"]}}]}
        self.assertEqual(
            collection._alias_filter(test_filter),
            {"$and": [{"my_elements": {"$in": ["A", "B", "C"]}}]},
        )
        test_filter = {"elements": "A"}
        self.assertEqual(collection._alias_filter(test_filter), {"my_elements": "A"})
        test_filter = ["A", "B", "C"]
        self.assertEqual(collection._alias_filter(test_filter), ["A", "B", "C"])
