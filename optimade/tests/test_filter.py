import os
from glob import glob
from unittest import TestCase

from lark import Tree, UnexpectedInput

from optimade.filter import Parser

testfile_dir = os.path.join(os.path.dirname(__file__), "testfiles")


class ParserTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_filters = []
        for fn in glob(os.path.join(testfile_dir, "*.inp")):
            with open(fn) as f:
                cls.test_filters.append(f.read().strip())

    def setUp(self):
        self.parser = Parser()

    def test_inputs(self):
        for tf in self.test_filters:
            if tf == "filter=number=0.0.1":
                self.assertRaises(UnexpectedInput, self.parser.parse, tf)
            else:
                tree = self.parser.parse(tf)
                self.assertTrue(tree, Tree)

    def test_parser_version(self):
        v = (0, 9, 5)
        p = Parser(version=v)
        self.assertIsInstance(p.parse("filter=n<3"), Tree)
        self.assertEqual(p.version, v)


