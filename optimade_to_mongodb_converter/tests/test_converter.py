import os
from testfiles.test_bank import number_test,syntax_tests, raiseErrors
from optimade_to_mongodb_converter.optimade_to_mongodb_converter import optimadeToMongoDBConverter
from glob import glob
from unittest import TestCase
class OptimadeToMongoDBConverterTest(TestCase):
    @classmethod
    def setUpClass(cls):
        return

    def setUp(self):
        self.testFilesPath = os.path.join(os.getcwd(),"testfiles")

    def test_all(self):
        #test for numerical correctness
        for t in number_test:
            self.assertEqual(optimadeToMongoDBConverter(t['query']), t['answer'], t['name'])
        # test for syntax correctness
        for t in syntax_tests:
            self.assertEqual(optimadeToMongoDBConverter(t['query']), t['answer'], t['name'])
        # test for raising errors
        for t in raiseErrors:
            self.assertRaises(Exception, optimadeToMongoDBConverter(t['query']))
