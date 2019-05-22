import os
from optimade.converter.mongoconverter.tests.test_bank import number_test, syntax_tests, raiseErrors
from optimade.converter.mongoconverter.mongo import optimadeToMongoDBConverter

from unittest import TestCase

from optimade.filter import Parser
from optimade.converter.mongoconverter.mongo import MongoTransformer, OptimadeToPQLTransformer


class OptimadeToMongoDBConverterTest(TestCase):
    @classmethod
    def setUpClass(cls):
        return
    
    def setUp(self):
        self.testFilesPath = os.path.join(os.getcwd(),"testfiles")
        
    def test_all(self):
        # test for numerical correctness
        for t in number_test:
            self.assertEqual(optimadeToMongoDBConverter(t['query'], aliases=t.get('aliases')), t['answer'], t['name'])
        # test for syntax correctness
        for t in syntax_tests:
            self.assertEqual(optimadeToMongoDBConverter(t['query'], aliases=t.get('aliases')), t['answer'], t['name'])
        # test for raising errors
        for t in raiseErrors:
            self.assertRaises(Exception, optimadeToMongoDBConverter(t['query'], aliases=t.get('aliases')))


class TestTransformer(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = Parser()
        cls.parse = cls._parser.parse
        cls.transformer = OptimadeToPQLTransformer()
        cls.transformer = cls.transformer.tranform

    def test_simple_comparisons(self):
        self.assertEqual(self.parse("a<3"), {"$lt": {"a": 3}})
        self.assertEqual(self.parse("a<=3"), {"$lte": {"a": 3}})
        self.assertEqual(self.parse("a>3"), {"$gt": {"a": 3}})
        self.assertEqual(self.parse("a>=3"), {"$gte": {"a": 3}})
        self.assertEqual(self.parse("a=3"), {"$eq": {"a": 3}})
        self.assertEqual(self.parse("a!=3"), {"$ne": {"a": 3}})

    def test_not(self):
        self.assertEqual(self.parse("not a<3"), {"$not": {"$lt": {"a": 3}}})
