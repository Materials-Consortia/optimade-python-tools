from unittest import TestCase

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

    def test_simple_comparisons(self):
        self.assertEqual(self.convert("a<3"), {"a": {"$lt": 3}})
        self.assertEqual(self.convert("a<=3"), {"a": {"$lte": 3}})
        self.assertEqual(self.convert("a>3"), {"a": {"$gt": 3}})
        self.assertEqual(self.convert("a>=3"), {"a": {"$gte": 3}})
        self.assertIn(self.convert("a=3"), [{"a": {"$eq": 3}}, {"a": 3}])
        self.assertEqual(self.convert("a!=3"), {"a": {"$ne": 3}})

    def test_not(self):
        self.assertEqual(self.convert("not a<3"), {"a": {"$not": {"$lt": 3}}})
