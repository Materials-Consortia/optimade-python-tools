import os
from glob import glob
from unittest import TestCase

from lark import Tree

from optimade.filterparser import LarkParser, ParserError

testfile_dir = os.path.join(os.path.dirname(__file__), "testfiles")


class ParserTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_filters = []
        for fn in glob(os.path.join(testfile_dir, "*.inp")):
            with open(fn) as f:
                cls.test_filters.append(f.read().strip())

    def setUp(self):
        self.parser = LarkParser(version=(0, 9, 5))

    def test_inputs(self):
        for tf in self.test_filters:
            if tf == "filter=number=0.0.1":
                self.assertRaises(ParserError, self.parser.parse, tf)
            else:
                tree = self.parser.parse(tf)
                self.assertTrue(tree, Tree)

    def test_parser_version(self):
        v = (0, 9, 5)
        p = LarkParser(version=v)
        self.assertIsInstance(p.parse(self.test_filters[0]), Tree)
        self.assertEqual(p.version, v)

    def test_repr(self):
        self.assertIsNotNone(repr(self.parser))
        self.parser.parse(self.test_filters[0])
        self.assertIsNotNone(repr(self.parser))


class FilterParserTest(TestCase):
    version = (0, 10, 0)
    variant = 'default'
    passes = (
        ' ',
        'NOT ( chemical_formula_hill = "Al" AND chemical_formula_anonymous = "A" OR chemical_formula_anonymous = "H2O" AND NOT chemical_formula_hill = "Ti" )',
        'nelements > 3',
        'chemical_formula_hill = "H2O" AND chemical_formula_anonymous != "AB"',
        '_exmpl_aax <= +.1e8 OR nelements >= 10 AND NOT ( _exmpl_x != "Some string" OR NOT _exmpl_a = 7)',
        '_exmpl_spacegroup="P2"',
        '_exmpl_cell_volume<100.0',
        '_exmpl_bandgap > 5.0 AND _exmpl_molecular_weight < 350',
        '_exmpl_melting_point<300 AND nelements=4 AND elements="Si,O2"',
        '_exmpl_some_string_property = 42',
        '5 < _exmpl_a',
        '((NOT (_exmpl_a>_exmpl_b)) AND _exmpl_x>0)',
        '5 < 7',
        'chemical_formula_anonymous CONTAINS "C2" AND chemical_formula_anonymous STARTS WITH "A2"',
        'chemical_formula_anonymous STARTS "B2" AND chemical_formula_anonymous ENDS WITH "D2"',
        'list HAS < 3',
        'list HAS ALL < 3, > 3',
        'list:list HAS >=2:<=5',
        'elements HAS "H" AND elements HAS ALL "H","He","Ga","Ta" AND elements HAS ONLY "H","He","Ga","Ta" AND elements HAS ANY "H", "He", "Ga", "Ta"',
        'elements HAS ONLY "H","He","Ga","Ta"',
        'elements:_exmpl_element_counts HAS "H":6 AND elements:_exmpl_element_counts HAS ALL "H":6,"He":7 AND elements:_exmpl_element_counts HAS ONLY "H":6 AND elements:_exmpl_element_counts HAS ANY "H":6,"He":7 AND elements:_exmpl_element_counts HAS ONLY "H":6,"He":7',
        '_exmpl_element_counts HAS < 3 AND _exmpl_element_counts HAS ANY > 3, = 6, 4, != 8',
        'elements:_exmpl_element_counts:_exmpl_element_weights HAS ANY > 3:"He":>55.3 , = 6:>"Ti":<37.6 , 8:<"Ga":0',
        'identifier1.identifierd2 = 42',
        'chemical_formula_hill IS KNOWN AND NOT chemical_formula_anonymous IS UNKNOWN',
        'NOT a > b OR c = 100 AND f = "C2 H6"',
        '(NOT (a > b)) OR ( (c = 100) AND (f = "C2 H6") )',
        'a >= 0 AND NOT b < c OR c = 0',
        '((a >= 0) AND (NOT (b < c))) OR (c = 0)',
        'te < st',
        'spacegroup="P2"',
        '_cod_cell_volume<100.0',
        '_mp_bandgap > 5.0 AND _cod_molecular_weight < 350',
        '_cod_melting_point<300 AND nelements=4 AND elements="Si,O2"',
        'number=0.ANDnumber=.0ANDnumber=0.0ANDnumber=+0ANDNUMBER=-0ANDnumber=0e1ANDnumber=0e-1ANDnumber=0e+1',
        'key=value',
        'author=" someone "',
        'NOTICE=val',
        'author="Sąžininga Žąsis"',
        'a = 12345 AND b = +12 AND c = -34 AND d = 1.2 AND e = .2E7 AND f = -.2E+7 AND g = +10.01E-10 AND h = 6.03e23 AND i = .1E1 AND j = -.1e1 AND k = 1.e-12 AND l = -.1e-12 AND m = 1000000000.E1000000000',
        'field = "!#$%&\'() * +, -./:; <= > ? @[] ^ `{|}~ % "',
    )
    fails = (
        'number=0.0.1',
    )

    def setUp(self):
        self.parser = LarkParser(version=self.version, variant=self.variant)

    def test_passes(self):
        for tf in self.passes:
            tree = self.parser.parse(tf)
            self.assertTrue(tree, Tree)

    def test_fails(self):
        for tf in self.fails:
            self.assertRaises(ParserError, self.parser.parse, tf)

    def test_parser_version(self):
        self.assertEqual(self.parser.version, self.version)
        self.assertEqual(self.parser.variant, self.variant)

    def test_repr(self):
        self.assertIsNotNone(repr(self.parser))
        self.parser.parse(self.passes[0])
        self.assertIsNotNone(repr(self.parser))
