import os
from glob import glob
from unittest import TestCase

from lark import Tree, UnexpectedInput

from optimade.filter import Parser

testfiles_dir = os.path.join(os.path.dirname(__file__), "testfiles")


class ParserTest(TestCase):
    @classmethod
    def setUpClass(cls):
        testfiles_names = glob(os.path.join(testfiles_dir, "*.inp"))
        cls.test_filters = []
        for fn in testfiles_names:
            with open(fn) as f:
                cls.test_filters.append(f.read().strip())

    def test_inputs(self):
        for tf in self.test_filters:
            p = Parser(tf)
            if tf == "filter=number=0.0.1":
                self.assertRaises(UnexpectedInput, p.parse)
            else:
                tree = p.parse()
                self.assertTrue(tree, Tree)


