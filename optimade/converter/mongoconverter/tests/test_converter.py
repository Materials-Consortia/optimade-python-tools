import itertools
from unittest import TestCase
import uuid

from pymongo import MongoClient

from optimade.filter import Parser
from optimade.converter.mongoconverter.mongo import MongoTransformer


class TestTransformer(TestCase):
    @classmethod
    def setUpClass(cls):
        parser = Parser()
        transformer = MongoTransformer()

        def convert(_, q):
            parsed = parser.parse(q)
            return transformer.transform(parsed)

        cls.convert = convert
        cls.client = MongoClient()
        cls.db = cls.client[f'test_db_{uuid.uuid4()}']
        cls.coll = cls.db.data
        cls.coll.insert_many([
            {"a": a, "b": b} for a, b in itertools.product(range(10), range(10))
        ])

    @classmethod
    def tearDownClass(cls):
        cls.client.drop_database(cls.db)
        cls.client.close()

    def test_simple_comparisons(self):
        self.assertEqual(self.convert("a<3"), {"a": {"$lt": 3}})
        self.assertEqual(self.convert("a<=3"), {"a": {"$lte": 3}})
        self.assertEqual(self.convert("a>3"), {"a": {"$gt": 3}})
        self.assertEqual(self.convert("a>=3"), {"a": {"$gte": 3}})
        self.assertIn(self.convert("a=3"), [{"a": {"$eq": 3}}, {"a": 3}])
        self.assertEqual(self.convert("a!=3"), {"a": {"$ne": 3}})

    def test_not(self):
        self.assertEqual(self.convert("not a<3"), {"a": {"$not": {"$lt": 3}}})

    def test_conjunctions(self):
        self.assertEqual(self.coll.count_documents(self.convert("a<5 and b=0")), 5)
        self.assertEqual(self.coll.count_documents(self.convert("a<5")), 5*10)
        docs = list(self.coll.find(self.convert("a<5 and b>=8"), {"_id": 0, "a": 1, "b": 1}))
        self.assertEqual(len(docs), 5 * 2)
        self.assertIn({"a": 4, "b": 9}, docs)
        # grammar evaluates conjunctions progressively rightwards.
        docs = list(self.coll.find(self.convert("a >= 8 or a<5 and b>=8"), {"_id": 0, "a": 1, "b": 1}))
        self.assertEqual(len(docs), 7 * 2)
        self.assertIn({"a": 4, "b": 9}, docs)
        self.assertIn({"a": 8, "b": 9}, docs)
