from unittest import TestCase

from optimade.filter import Parser
from optimade.converter.mongoconverter.mongo import MongoTransformer, optimadeToMongoDBConverter


class TestTransformer(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = Parser()
        cls.parse = cls.parser.parse
        cls.transformer = MongoTransformer
        cls.transform = cls.transformer.transform
        #cls.convert = lambda q: cls.transform(cls.parse(q))
        cls.convert = lambda _, q: optimadeToMongoDBConverter(q)

    def test_simple_comparisons(self):
        self.assertEqual(self.convert("filter=a<3"), {"a": {"$lt": 3}})
        self.assertEqual(self.convert("filter=a<=3"), {"a": {"$lte": 3}})
        self.assertEqual(self.convert("filter=a>3"), {"a": {"$gt": 3}})
        self.assertEqual(self.convert("filter=a>=3"), {"a": {"$gte": 3}})
        self.assertIn(self.convert("filter=a=3"), [{"a": {"$eq": 3}}, {"a": 3}])
        self.assertEqual(self.convert("filter=a!=3"), {"a": {"$ne": 3}})

    def test_not(self):
        self.assertEqual(self.convert("filter=not a<3"), {"$not": {"a": {"$lt": 3}}})
