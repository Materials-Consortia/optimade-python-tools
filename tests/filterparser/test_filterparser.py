import os
from glob import glob
import unittest

from lark import Tree

from optimade.filterparser import LarkParser, ParserError

testfile_dir = os.path.join(os.path.dirname(__file__), "testfiles")


class ParserTestV0_9_5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_filters = []
        for fn in sorted(glob(os.path.join(testfile_dir, "*.inp"))):
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


class ParserTestV0_10_1(unittest.TestCase):
    version = (0, 10, 1)
    variant = "default"

    @classmethod
    def setUpClass(cls):
        cls.parser = LarkParser(version=cls.version, variant=cls.variant)

    def parse(self, inp):
        return self.parser.parse(inp)

    def test_empty(self):
        self.assertIsInstance(self.parse(" "), Tree)

    def test_property_names(self):
        self.assertIsInstance(self.parse("band_gap = 1"), Tree)
        self.assertIsInstance(self.parse("cell_length_a = 1"), Tree)
        self.assertIsInstance(self.parse("cell_volume = 1"), Tree)

        with self.assertRaises(ParserError):
            self.parse("0_kvak IS KNOWN")  # starts with a number

        with self.assertRaises(ParserError):
            self.parse('"foo bar" IS KNOWN')  # contains space; contains quotes

        with self.assertRaises(ParserError):
            self.parse("BadLuck IS KNOWN")  # contains upper-case letters

        # database-provider-specific prefixes
        self.assertIsInstance(self.parse("_exmpl_formula_sum = 1"), Tree)
        self.assertIsInstance(self.parse("_exmpl_band_gap = 1"), Tree)

        # Nested property names
        self.assertIsInstance(self.parse("identifier1.identifierd2 = 42"), Tree)

    def test_string_values(self):
        self.assertIsInstance(self.parse('author="Sąžininga Žąsis"'), Tree)
        self.assertIsInstance(
            self.parse('field = "!#$%&\'() * +, -./:; <= > ? @[] ^ `{|}~ % "'), Tree
        )

    def test_number_values(self):
        self.assertIsInstance(self.parse("a = 12345"), Tree)
        self.assertIsInstance(self.parse("b = +12"), Tree)
        self.assertIsInstance(self.parse("c = -34"), Tree)
        self.assertIsInstance(self.parse("d = 1.2"), Tree)
        self.assertIsInstance(self.parse("e = .2E7"), Tree)
        self.assertIsInstance(self.parse("f = -.2E+7"), Tree)
        self.assertIsInstance(self.parse("g = +10.01E-10"), Tree)
        self.assertIsInstance(self.parse("h = 6.03e23"), Tree)
        self.assertIsInstance(self.parse("i = .1E1"), Tree)
        self.assertIsInstance(self.parse("j = -.1e1"), Tree)
        self.assertIsInstance(self.parse("k = 1.e-12"), Tree)
        self.assertIsInstance(self.parse("l = -.1e-12"), Tree)
        self.assertIsInstance(self.parse("m = 1000000000.E1000000000"), Tree)

        with self.assertRaises(ParserError):
            self.parse("number=1.234D12")
        with self.assertRaises(ParserError):
            self.parse("number=.e1")
        with self.assertRaises(ParserError):
            self.parse("number= -.E1")
        with self.assertRaises(ParserError):
            self.parse("number=+.E2")
        with self.assertRaises(ParserError):
            self.parse("number=1.23E+++")
        with self.assertRaises(ParserError):
            self.parse("number=+-123")
        with self.assertRaises(ParserError):
            self.parse("number=0.0.1")

    def test_operators(self):
        # Basic boolean operations
        self.assertIsInstance(
            self.parse(
                'NOT ( chemical_formula_hill = "Al" AND chemical_formula_anonymous = "A" OR '
                'chemical_formula_anonymous = "H2O" AND NOT chemical_formula_hill = "Ti" )'
            ),
            Tree,
        )

        # Numeric and String comparisons
        self.assertIsInstance(self.parse("nelements > 3"), Tree)
        self.assertIsInstance(
            self.parse(
                'chemical_formula_hill = "H2O" AND chemical_formula_anonymous != "AB"'
            ),
            Tree,
        )
        self.assertIsInstance(
            self.parse(
                "_exmpl_aax <= +.1e8 OR nelements >= 10 AND "
                'NOT ( _exmpl_x != "Some string" OR NOT _exmpl_a = 7)'
            ),
            Tree,
        )
        self.assertIsInstance(self.parse('_exmpl_spacegroup="P2"'), Tree)
        self.assertIsInstance(self.parse("_exmpl_cell_volume<100.0"), Tree)
        self.assertIsInstance(
            self.parse("_exmpl_bandgap > 5.0 AND _exmpl_molecular_weight < 350"), Tree
        )
        self.assertIsInstance(
            self.parse('_exmpl_melting_point<300 AND nelements=4 AND elements="Si,O2"'),
            Tree,
        )
        self.assertIsInstance(self.parse("_exmpl_some_string_property = 42"), Tree)
        self.assertIsInstance(self.parse("5 < _exmpl_a"), Tree)

        # OPTIONAL
        self.assertIsInstance(
            self.parse("((NOT (_exmpl_a>_exmpl_b)) AND _exmpl_x>0)"), Tree
        )
        self.assertIsInstance(self.parse("5 < 7"), Tree)

    def test_id(self):
        self.assertIsInstance(self.parse('id="example/1"'), Tree)
        self.assertIsInstance(self.parse('"example/1" = id'), Tree)
        self.assertIsInstance(self.parse('id="test/2" OR "example/1" = id'), Tree)

    def test_string_operations(self):
        #  Substring comparisons
        self.assertIsInstance(
            self.parse(
                'chemical_formula_anonymous CONTAINS "C2" AND '
                'chemical_formula_anonymous STARTS WITH "A2"'
            ),
            Tree,
        )
        self.assertIsInstance(
            self.parse(
                'chemical_formula_anonymous STARTS "B2" AND '
                'chemical_formula_anonymous ENDS WITH "D2"'
            ),
            Tree,
        )

    def test_list_properties(self):
        # Comparisons of list properties
        self.assertIsInstance(self.parse("list HAS < 3"), Tree)
        self.assertIsInstance(self.parse("list HAS ALL < 3, > 3"), Tree)
        self.assertIsInstance(self.parse("list:list HAS >=2:<=5"), Tree)
        self.assertIsInstance(
            self.parse(
                'elements HAS "H" AND elements HAS ALL "H","He","Ga","Ta" AND elements HAS '
                'ONLY "H","He","Ga","Ta" AND elements HAS ANY "H", "He", "Ga", "Ta"'
            ),
            Tree,
        )

        # OPTIONAL:
        self.assertIsInstance(self.parse('elements HAS ONLY "H","He","Ga","Ta"'), Tree)
        self.assertIsInstance(self.parse('elements HAS ALL "H","He","Ga","Ta"'), Tree)
        self.assertIsInstance(self.parse('elements HAS ANY "H","He","Ga","Ta"'), Tree)
        self.assertIsInstance(
            self.parse(
                'elements:_exmpl_element_counts HAS "H":6 AND '
                'elements:_exmpl_element_counts HAS ALL "H":6,"He":7 AND '
                'elements:_exmpl_element_counts HAS ONLY "H":6 AND '
                'elements:_exmpl_element_counts HAS ANY "H":6,"He":7 AND '
                'elements:_exmpl_element_counts HAS ONLY "H":6,"He":7'
            ),
            Tree,
        )
        self.assertIsInstance(
            self.parse(
                "_exmpl_element_counts HAS < 3 AND "
                "_exmpl_element_counts HAS ANY > 3, = 6, 4, != 8"
            ),
            Tree,
        )
        self.assertIsInstance(
            self.parse(
                "elements:_exmpl_element_counts:_exmpl_element_weights "
                'HAS ANY > 3:"He":>55.3 , = 6:>"Ti":<37.6 , 8:<"Ga":0'
            ),
            Tree,
        )

    def test_properties(self):
        #  Filtering on Properties with unknown value
        self.assertIsInstance(
            self.parse(
                "chemical_formula_hill IS KNOWN AND "
                "NOT chemical_formula_anonymous IS UNKNOWN"
            ),
            Tree,
        )

    def test_precedence(self):
        self.assertIsInstance(self.parse('NOT a > b OR c = 100 AND f = "C2 H6"'), Tree)
        self.assertIsInstance(
            self.parse('(NOT (a > b)) OR ( (c = 100) AND (f = "C2 H6") )'), Tree
        )
        self.assertIsInstance(self.parse("a >= 0 AND NOT b < c OR c = 0"), Tree)
        self.assertIsInstance(
            self.parse("((a >= 0) AND (NOT (b < c))) OR (c = 0)"), Tree
        )

    def test_special_cases(self):
        self.assertIsInstance(self.parse("te < st"), Tree)
        self.assertIsInstance(self.parse('spacegroup="P2"'), Tree)
        self.assertIsInstance(self.parse("_cod_cell_volume<100.0"), Tree)
        self.assertIsInstance(
            self.parse("_mp_bandgap > 5.0 AND _cod_molecular_weight < 350"), Tree
        )
        self.assertIsInstance(
            self.parse('_cod_melting_point<300 AND nelements=4 AND elements="Si,O2"'),
            Tree,
        )
        self.assertIsInstance(self.parse("key=value"), Tree)
        self.assertIsInstance(self.parse('author=" someone "'), Tree)
        self.assertIsInstance(self.parse('author=" som\neone "'), Tree)
        self.assertIsInstance(
            self.parse(
                "number=0.ANDnumber=.0ANDnumber=0.0ANDnumber=+0AND_n_u_m_b_e_r_=-0AND"
                "number=0e1ANDnumber=0e-1ANDnumber=0e+1"
            ),
            Tree,
        )

        self.assertIsInstance(
            self.parse("NOTice=val"), Tree
        )  # property (ice) != property (val)
        self.assertIsInstance(
            self.parse('NOTice="val"'), Tree
        )  # property (ice) != value ("val")
        self.assertIsInstance(
            self.parse('"NOTice"=val'), Tree
        )  # value ("NOTice") = property (val)

        with self.assertRaises(ParserError):
            self.parse("NOTICE=val")  # not valid property or value (NOTICE)
        with self.assertRaises(ParserError):
            self.parse('"NOTICE"=Val')  # not valid property (Val)
        with self.assertRaises(ParserError):
            self.parse("NOTICE=val")  # not valid property or value (NOTICE)

    def test_parser_version(self):
        self.assertEqual(self.parser.version, self.version)
        self.assertEqual(self.parser.variant, self.variant)

    def test_repr(self):
        self.assertIsNotNone(repr(self.parser))
        self.parser.parse('key="value"')
        self.assertIsNotNone(repr(self.parser))
