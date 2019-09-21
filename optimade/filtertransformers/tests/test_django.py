import json
from optimade.filtertransformers.django import Lark2Django
from django.test import TestCase
import os

test_data = [( "band_gap<1","(AND: ('calculation__band_gap__lt', '1'))"),
             ( "a >= 8 or a<5 and b>=8",
               "(AND: (OR: ('entry__natoms__gte', '8'), ('entry__composition__ntypes__lt', '5')), ('stability__lte', '0'))"),
             ( "NOT natoms >= 8","(NOT (AND: ('entry__natoms__gte', '8')))"),
             ( "element = Th AND element != Na ",
               "(AND: ('composition__element_list__contains', 'Th'), (NOT (AND: ('composition__element_list__contains', 'Na'))))")]

class DjangoParserTest(TestCase):
    def SetUp(self):
        self.Transformer = Lark2Django()
    def test_query_conversion(self):
        for raw_q,dj_q in test_data.keys():
            parsed_tree = self.Transformer.parse_raw_q(raw_q)
            self.assertEqual(str(self.Transformer.evaluate(parsed_tree)), dj_q)
