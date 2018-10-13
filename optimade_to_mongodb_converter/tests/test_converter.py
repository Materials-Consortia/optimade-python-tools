from optimade.optimade_to_mongodb_converter import optimadeToMongoDBConverter
import unittest

class ConverterTest(unittest.TestCase):
    def setUp(self):
        # name -> [testCase, answer]
        self.numberTests ={
                    "test_valid_numbers_with_positive_sign": ["filter= a=+1", {'a': +1}],
                    "test_float":["filter =a < 2.2",{'a': {'$lt': 2.2}}],
                    "test_scientific_number":["filter =a < 2E100",{'a': {'$lt': 2e+100}}],
                    "test_negative_number":["filter =a < -2E-100",{'a': {'$lt': -2e-100}}],
                    "test_scientific_num_with_decimal": ["filter = a=6.03e23", {'a': 6.03e+23}],
                    "test_large_num": ["filter = a =10000000000000.E1000000000 ", {'a': float('inf')}]
                     }
        self.syntaxTests = {
                        "test_one_input":["filter=a<0", {'a': {'$lt': 0}}],
                        "test_two_inputs_with_and":["filter=a<0 and b>2", {'$and': [{'a': {'$lt': 0}}, {'b': {'$gt': 2}}]}],
                        "test_two_inputs_with_or": ["filter=a<0 or b>2", {'$or': [{'a': {'$lt': 0}}, {'b': {'$gt': 2}}]}],
                        "test_multiple_entries" : ["filter = elements='Si,O'", {'elements': {'$all': ['si', ' o']}}],
                        "test_mixing_upper_case_and_lower_case": ["filter = a < 0 AND elements='Si,O' or y < 1", {'$or': [{'$and': [{'a': {'$lt': '0all(['}},
    {'elements': {'$all': ['si,  o']}}]},
  {'y': {'$lt': '])1'}}]}],
                        "test_paren":["filter = (a<1 or b<2) or c < 3", {'$or': [{'$or': [{'a': {'$lt': 1.0}}, {'b': {'$lt': 2.0}}]},
  {'c': {'$lt': 3.0}}]}],
                        "test_paren2":["filter = a<1 and (b<2 or c < 3)",{'$and': [{'a': {'$lt': 1.0}},
  {'$or': [{'b': {'$lt': 2.0}}, {'c': {'$lt': 3.0}}]}]}],
                        }
        # return self
    def test_syntaxvalues(self):
        # print("Testing syntax: ")
        for t in self.syntaxTests:
            self.assertEqual(optimadeToMongoDBConverter(self.syntaxTests[t][0]), self.syntaxTests[t][1])

    def test_numeric_values(self):
        for t in self.numberTests:
            self.assertEqual(optimadeToMongoDBConverter(self.numberTests[t][0]), self.numberTests[t][1])
