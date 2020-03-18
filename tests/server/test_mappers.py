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
