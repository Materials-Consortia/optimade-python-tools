import os
from unittest import TestCase

from optimade.converter.mongoconverter.tests.test_bank import number_test, syntax_tests, raiseErrors
from optimade.converter.mongoconverter.mongo import optimadeToMongoDBConverter


class OptimadeToMongoDBConverterTest(TestCase):
    @classmethod
    def setUpClass(cls):
        return

    def setUp(self):
        self.testFilesPath = os.path.join(os.getcwd() ,"testfiles")

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
