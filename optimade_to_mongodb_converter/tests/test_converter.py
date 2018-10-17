import sys, os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), "optimade_to_mongodb_converter"))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), "optimade"))

from optimade_to_mongodb_converter import optimadeToMongoDBConverter
from glob import glob
from unittest import TestCase
class OptimadeToMongoDBConverterTest(TestCase):
    @classmethod
    def setUpClass(cls):
        return
    def setUp(self):
        self.testFilesPath = os.path.join(os.getcwd(),"testfiles")
    def test_all(self):
        for fn in glob(os.path.join(self.testFilesPath, "*.inp")):
            with open(fn) as fp:
                for cnt, line in enumerate(fp):
                    array = line.split("|")
                    self.assertEqual(str(optimadeToMongoDBConverter(array[1])), array[2].lstrip()[:-1])
    def test_error(self):
        for fn in glob(os.path.join(self.testFilesPath, "*.err")):
            with open(fn) as fp:
                for cnt, line in enumerate(fp):
                    self.assertRaises(Exception, optimadeToMongoDBConverter(line))