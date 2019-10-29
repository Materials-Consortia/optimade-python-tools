import unittest
from optimade.filterparser import LarkParser, ParserError
from optimade.filtertransformers.mongo import NewMongoTransformer


class TestMongoTransformer(unittest.TestCase):
    version = (0, 10, 0)
    variant = 'default'

    def setUp(self):
        p = LarkParser(version=self.version, variant=self.variant)
        t = NewMongoTransformer()
        self.transform = lambda inp: t.transform(p.parse(inp))

    def test_empty(self):
        self.assertIsNone(self.transform(' '))

    def test_property_names(self):
        self.assertEqual(self.transform('band_gap = 1'), {'band_gap': {'$eq': 1}})
        self.assertEqual(self.transform('cell_length_a = 1'), {'cell_length_a': {'$eq': 1}})
        self.assertEqual(self.transform('cell_volume = 1'), {'cell_volume': {'$eq': 1}})

        with self.assertRaises(ParserError):
            self.transform('0_kvak = 1')  # starts with a number

        # with self.assertRaises(ParserError):
        #     self.transform('"foo bar" = 1')  # contains space; contains quotes

        # with self.assertRaises(ParserError):
        #     self.transform('BadLuck = 1')  # contains upper-case letters

        # database-provider-specific prefixes
        self.assertEqual(self.transform('_exmpl_formula_sum = 1'), {'_exmpl_formula_sum': {'$eq': 1}})
        self.assertEqual(self.transform('_exmpl_band_gap = 1'), {'_exmpl_band_gap': {'$eq': 1}})

        # Nested property names
        self.assertEqual(self.transform('identifier1.identifierd2 = 42'), {'identifier1.identifierd2': {'$eq': 42}})

    def test_string_values(self):
        self.assertEqual(self.transform('author="Sąžininga Žąsis"'), {'author': {'$eq': 'Sąžininga Žąsis'}})
        self.assertEqual(self.transform('field = "!#$%&\'() * +, -./:; <= > ? @[] ^ `{|}~ % "'),
                         {'field': {'$eq': '!#$%&\'() * +, -./:; <= > ? @[] ^ `{|}~ % '}})

    def test_number_values(self):
        self.assertEqual(self.transform('a = 12345'), {'a': {'$eq': 12345}})
        self.assertEqual(self.transform('b = +12'), {'b': {'$eq': 12}})
        self.assertEqual(self.transform('c = -34'), {'c': {'$eq': -34}})
        self.assertEqual(self.transform('d = 1.2'), {'d': {'$eq': 1.2}})
        self.assertEqual(self.transform('e = .2E7'), {'e': {'$eq': 2000000.0}})
        self.assertEqual(self.transform('f = -.2E+7'), {'f': {'$eq': -2000000.0}})
        self.assertEqual(self.transform('g = +10.01E-10'), {'g': {'$eq': 1.001e-09}})
        self.assertEqual(self.transform('h = 6.03e23'), {'h': {'$eq': 6.03e+23}})
        self.assertEqual(self.transform('i = .1E1'), {'i': {'$eq': 1.0}})
        self.assertEqual(self.transform('j = -.1e1'), {'j': {'$eq': -1.0}})
        self.assertEqual(self.transform('k = 1.e-12'), {'k': {'$eq': 1e-12}})
        self.assertEqual(self.transform('l = -.1e-12'), {'l': {'$eq': -1e-13}})
        self.assertEqual(self.transform('m = 1000000000.E1000000000'), {'m': {'$eq': float('inf')}})

        with self.assertRaises(ParserError):
            self.transform('number=1.234D12')
        with self.assertRaises(ParserError):
            self.transform('number=.e1')
        with self.assertRaises(ParserError):
            self.transform('number= -.E1')
        with self.assertRaises(ParserError):
            self.transform('number=+.E2')
        with self.assertRaises(ParserError):
            self.transform('number=1.23E+++')
        with self.assertRaises(ParserError):
            self.transform('number=+-123')
        with self.assertRaises(ParserError):
            self.transform('number=0.0.1')

    def test_simple_comparisons(self):
        self.assertEqual(self.transform("a<3"), {"a": {"$lt": 3}})
        self.assertEqual(self.transform("a<=3"), {"a": {"$lte": 3}})
        self.assertEqual(self.transform("a>3"), {"a": {"$gt": 3}})
        self.assertEqual(self.transform("a>=3"), {"a": {"$gte": 3}})
        self.assertEqual(self.transform("a=3"), {"a": {"$eq": 3}})
        self.assertEqual(self.transform("a!=3"), {"a": {"$ne": 3}})

    def test_operators(self):
        # Basic boolean operations
        # TODO: {"a": {"$not": {"$lt": 3}}} can be simplified to {"a": {"$gte": 3}}
        self.assertEqual(self.transform("NOT a<3"), {"a": {"$not": {"$lt": 3}}})

        # TODO: {'$not': {'$eq': 'Ti'}} can be simplified to {'$ne': 'Ti'}
        self.assertEqual(self.transform('NOT ( chemical_formula_hill = "Al" AND chemical_formula_anonymous = "A" OR '
                                        'chemical_formula_anonymous = "H2O" AND NOT chemical_formula_hill = "Ti" )'),
                         {'$or': {'$not': [{'$and': [{'chemical_formula_hill': {'$eq': 'Al'}},
                                                     {'chemical_formula_anonymous': {'$eq': 'A'}}]},
                                           {'$and': [{'chemical_formula_anonymous': {'$eq': 'H2O'}},
                                                     {'chemical_formula_hill': {'$not': {'$eq': 'Ti'}}}]}]}})

        # Numeric and String comparisons
        self.assertEqual(self.transform('nelements > 3'), {'nelements': {'$gt': 3}})
        self.assertEqual(self.transform('chemical_formula_hill = "H2O" AND chemical_formula_anonymous != "AB"'),
                         {'$and': [{'chemical_formula_hill': {'$eq': 'H2O'}},
                                   {'chemical_formula_anonymous': {'$ne': 'AB'}}]})
        self.assertEqual(self.transform('_exmpl_aax <= +.1e8 OR nelements >= 10 AND '
                                        'NOT ( _exmpl_x != "Some string" OR NOT _exmpl_a = 7)'),
                         {'$or': [{'_exmpl_aax': {'$lte': 10000000.0}},
                                  {'$and': [{'nelements': {'$gte': 10}},
                                            {'$or': {'$not': [{'_exmpl_x': {'$ne': 'Some string'}},
                                                              {'_exmpl_a': {'$not': {'$eq': 7}}}]}}]}]})
        self.assertEqual(self.transform('_exmpl_spacegroup="P2"'), {'_exmpl_spacegroup': {'$eq': 'P2'}})
        self.assertEqual(self.transform('_exmpl_cell_volume<100.0'), {'_exmpl_cell_volume': {'$lt': 100.0}})
        self.assertEqual(self.transform('_exmpl_bandgap > 5.0 AND _exmpl_molecular_weight < 350'),
                         {'$and': [{'_exmpl_bandgap': {'$gt': 5.0}}, {'_exmpl_molecular_weight': {'$lt': 350}}]})
        self.assertEqual(self.transform('_exmpl_melting_point<300 AND nelements=4 AND elements="Si,O2"'),
                         {'$and': [{'_exmpl_melting_point': {'$lt': 300}}, {'nelements': {'$eq': 4}},
                                   {'elements': {'$eq': 'Si,O2'}}]})
        self.assertEqual(self.transform('_exmpl_some_string_property = 42'), {'_exmpl_some_string_property': {'$eq': 42}})
        self.assertEqual(self.transform('5 < _exmpl_a'), {'_exmpl_a': {'$lt': 5}})

        self.assertEqual(self.transform("a<5 AND b=0"), {'$and': [{'a': {'$lt': 5}}, {'b': {'$eq': 0}}]})
        self.assertEqual(self.transform("a >= 8 OR a<5 AND b>=8"),
                         {'$or': [{'a': {'$gte': 8}}, {'$and': [{'a': {'$lt': 5}}, {'b': {'$gte': 8}}]}]})

        # OPTIONAL
        # self.assertEqual(self.transform('((NOT (_exmpl_a>_exmpl_b)) AND _exmpl_x>0)'), {})
        # self.assertEqual(self.transform('5 < 7'), {})

    @unittest.skip('Not implemented yet.')
    def test_list_properties(self):
        # Comparisons of list properties
        self.assertEqual(self.transform('list HAS < 3'), {})
        self.assertEqual(self.transform('list HAS ALL < 3, > 3'), {})
        self.assertEqual(self.transform('list:list HAS >=2:<=5'), {})
        self.assertEqual(self.transform('elements HAS "H" AND elements HAS ALL "H","He","Ga","Ta" AND elements HAS '
                                        'ONLY "H","He","Ga","Ta" AND elements HAS ANY "H", "He", "Ga", "Ta"'), {})

        # OPTIONAL:
        self.assertEqual(self.transform('elements HAS ONLY "H","He","Ga","Ta"'), {})
        self.assertEqual(self.transform('elements:_exmpl_element_counts HAS "H":6 AND elements:_exmpl_element_counts '
                                        'HAS ALL "H":6,"He":7 AND elements:_exmpl_element_counts HAS ONLY "H":6 AND '
                                        'elements:_exmpl_element_counts HAS ANY "H":6,"He":7 AND '
                                        'elements:_exmpl_element_counts HAS ONLY "H":6,"He":7'), {})
        self.assertEqual(self.transform('_exmpl_element_counts HAS < 3 AND _exmpl_element_counts '
                                        'HAS ANY > 3, = 6, 4, != 8'), {})
        self.assertEqual(self.transform('elements:_exmpl_element_counts:_exmpl_element_weights '
                                        'HAS ANY > 3:"He":>55.3 , = 6:>"Ti":<37.6 , 8:<"Ga":0'), {})

    def test_properties(self):
        #  Filtering on Properties with unknown value
        # TODO: {'$not': {'$exists': False}} can be simplified to {'$exists': True}
        self.assertEqual(self.transform('chemical_formula_hill IS KNOWN AND NOT chemical_formula_anonymous IS UNKNOWN'),
                         {'$and': [{'chemical_formula_hill': {'$exists': True}},
                                   {'chemical_formula_anonymous': {'$not': {'$exists': False}}}]})

    def test_precedence(self):
        self.assertEqual(self.transform('NOT a > b OR c = 100 AND f = "C2 H6"'),
                         {'$or': [{'a': {'$not': {'$gt': 'b'}}},
                                  {'$and': [{'c': {'$eq': 100}}, {'f': {'$eq': 'C2 H6'}}]}]})
        self.assertEqual(self.transform('NOT a > b OR c = 100 AND f = "C2 H6"'),
                         self.transform('(NOT (a > b)) OR ( (c = 100) AND (f = "C2 H6") )'))
        self.assertEqual(self.transform('a >= 0 AND NOT b < c OR c = 0'),
                         self.transform('((a >= 0) AND (NOT (b < c))) OR (c = 0)'))

    def test_special_cases(self):
        self.assertEqual(self.transform('te < st'), {'te': {'$lt': 'st'}})
        self.assertEqual(self.transform('spacegroup="P2"'), {'spacegroup': {'$eq': 'P2'}})
        self.assertEqual(self.transform('_cod_cell_volume<100.0'), {'_cod_cell_volume': {'$lt': 100.0}})
        self.assertEqual(self.transform('_mp_bandgap > 5.0 AND _cod_molecular_weight < 350'),
                         {'$and': [{'_mp_bandgap': {'$gt': 5.0}}, {'_cod_molecular_weight': {'$lt': 350}}]})
        self.assertEqual(self.transform('_cod_melting_point<300 AND nelements=4 AND elements="Si,O2"'),
                         {'$and': [{'_cod_melting_point': {'$lt': 300}}, {'nelements': {'$eq': 4}},
                                   {'elements': {'$eq': 'Si,O2'}}]})
        self.assertEqual(self.transform('key=value'), {'key': {'$eq': 'value'}})
        self.assertEqual(self.transform('author=" someone "'), {'author': {'$eq': ' someone '}})
        self.assertEqual(self.transform('NOTICE=val'), {'ICE': {'$not': {'$eq': 'val'}}})
        self.assertEqual(self.transform('number=0.ANDnumber=.0ANDnumber=0.0ANDnumber=+0ANDNUMBER=-0ANDnumber=0e1AND'
                                        'number=0e-1ANDnumber=0e+1'),
                         {'$and': [{'number': {'$eq': 0.0}}, {'number': {'$eq': 0.0}}, {'number': {'$eq': 0.0}},
                                   {'number': {'$eq': 0}}, {'NUMBER': {'$eq': 0}}, {'number': {'$eq': 0.0}},
                                   {'number': {'$eq': 0.0}}, {'number': {'$eq': 0.0}}]})
