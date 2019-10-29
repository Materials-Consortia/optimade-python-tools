import unittest
from optimade.filterparser import LarkParser
from optimade.filtertransformers.mongo import NewMongoTransformer


class TestMongoTransformer(unittest.TestCase):
    version = (0, 10, 0)
    variant = 'default'

    def setUp(self):
        p = LarkParser(version=self.version, variant=self.variant)
        t = NewMongoTransformer()
        self.transform = lambda inp: t.transform(p.parse(inp))

    def tete_empty(self):
        self.assertIsNone(self.transform(' '))

    def test_simple_comparisons(self):
        self.assertEqual(self.transform("a<3"), {"a": {"$lt": 3}})
        self.assertEqual(self.transform("a<=3"), {"a": {"$lte": 3}})
        self.assertEqual(self.transform("a>3"), {"a": {"$gt": 3}})
        self.assertEqual(self.transform("a>=3"), {"a": {"$gte": 3}})
        self.assertIn(self.transform("a=3"), [{"a": {"$eq": 3}}, {"a": 3}])
        self.assertEqual(self.transform("a!=3"), {"a": {"$ne": 3}})

    def test_not(self):
        self.assertEqual(self.transform("NOT a<3"), {"a": {"$not": {"$lt": 3}}})

    def test_conjunctions(self):
        self.assertEqual(self.transform("a<5 AND b=0"),
                         {'$and': [{'a': {'$lt': 5}}, {'b': {'$eq': 0}}]})
        self.assertEqual(self.transform("a >= 8 OR a<5 AND b>=8"),
                         {'$or': [{'a': {'$gte': 8}}, {'$and': [{'a': {'$lt': 5}}, {'b': {'$gte': 8}}]}]})

    def test_should_pass(self):
        self.assertEqual(self.transform('te < st'), {'te': {'$lt': 'st'}})
        self.assertEqual(self.transform('spacegroup="P2"'), {'spacegroup': {'$eq': 'P2'}})
        self.assertEqual(self.transform('_cod_cell_volume<100.0'), {'_cod_cell_volume': {'$lt': 100.0}})
        self.assertEqual(
            self.transform('_mp_bandgap > 5.0 AND _cod_molecular_weight < 350'),
            {'$and': [{'_mp_bandgap': {'$gt': 5.0}}, {'_cod_molecular_weight': {'$lt': 350}}]})
        self.assertEqual(
            self.transform('_cod_melting_point<300 AND nelements=4 AND elements="Si,O2"'),
            {'$and': [{'_cod_melting_point': {'$lt': 300}}, {'nelements': {'$eq': 4}}, {'elements': {'$eq': 'Si,O2'}}]})
        self.assertEqual(
            self.transform('number=0.ANDnumber=.0ANDnumber=0.0AND'
                           'number=+0ANDNUMBER=-0ANDnumber=0e1AND'
                           'number=0e-1ANDnumber=0e+1'),
            {'$and': [{'number': {'$eq': 0.0}}, {'number': {'$eq': 0.0}}, {'number': {'$eq': 0.0}},
                      {'number': {'$eq': 0}}, {'NUMBER': {'$eq': 0}}, {'number': {'$eq': 0.0}},
                      {'number': {'$eq': 0.0}}, {'number': {'$eq': 0.0}}]})
        self.assertEqual(self.transform('key=value'), {'key': {'$eq': 'value'}})
        self.assertEqual(self.transform('author=" someone "'), {'author': {'$eq': ' someone '}})
        self.assertEqual(self.transform('author="Sąžininga Žąsis"'), {'author': {'$eq': 'Sąžininga Žąsis'}})
        self.assertEqual(
            self.transform('a = 12345 AND b = +12 AND c = -34 AND d = 1.2 AND e = .2E7 AND f = -.2E+7 AND '
                           'g = +10.01E-10 AND h = 6.03e23 AND i = .1E1 AND j = -.1e1 AND k = 1.e-12 AND '
                           'l = -.1e-12 AND m = 1000000000.E1000000000'),
            {'$and': [{'a': {'$eq': 12345}}, {'b': {'$eq': 12}}, {'c': {'$eq': -34}}, {'d': {'$eq': 1.2}},
                      {'e': {'$eq': 2000000.0}}, {'f': {'$eq': -2000000.0}}, {'g': {'$eq': 1.001e-09}},
                      {'h': {'$eq': 6.03e+23}}, {'i': {'$eq': 1.0}}, {'j': {'$eq': -1.0}},
                      {'k': {'$eq': 1e-12}}, {'l': {'$eq': -1e-13}}, {'m': {'$eq': float('inf')}}]})
        self.assertEqual(self.transform('field = "!#$%&\'() * +, -./:; <= > ? @[] ^ `{|}~ % "'),
                         {'field': {'$eq': "!#$%&'() * +, -./:; <= > ? @[] ^ `{|}~ % "}})
        self.assertEqual(self.transform('NOTICE=val'), {'ICE': {'$not': {'$eq': 'val'}}})
