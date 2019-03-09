import requests
from urlGenerator import generate
from unittest import TestCase

class OptimadeTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.endpoint = "http://127.0.0.1:5000/optimade/0.9.6/structures"
    # def test_structures_arg_parse(self):
    #     argument = f"{self.base_url}/structures/?elements=Au&nelements=3"
    #     print(argument)
    #     rv = requests.get(argument)
    #     self.assertEqual(rv.json(), {
    #       "elements": "Au",
    #       "nelements": 3
    #     })
    ### THIS IS NOT WORKING YET ###
    def test_full_url(self):
        params = {
            "filter": "nelements<3",
            "response_format": "jsonapi",
            "email_address": "dwinston@lbl.gov",
            "response_limit": "10",
            "response_fields": "id,nelements,material_id,elements,formula_prototype",
            "sort": "-nelements",
        }
        argument = generate(self.endpoint, params)
        rv = requests.get(argument)
        self.assertEqual(rv.json(), {'data': [{'type': 'structure', 'attributes': {'pretty_formula': 'TiO2', 'elements': ['O', 'Ti'], 'nelements': 2, 'material_id': 'mp-775938'}}, {'type': 'structure', 'attributes': {'pretty_formula': 'TiO2', 'elements': ['O', 'Ti'], 'nelements': 2, 'material_id': 'mp-766454'}}, {'type': 'structure', 'attributes': {'pretty_formula': 'TiO2', 'elements': ['O', 'Ti'], 'nelements': 2, 'material_id': 'mp-9173'}}, {'type': 'structure', 'attributes': {'pretty_formula': 'Ti6O', 'elements': ['O', 'Ti'], 'nelements': 2, 'material_id': 'mp-882'}}, {'type': 'structure', 'attributes': {'pretty_formula': 'TiO2', 'elements': ['O', 'Ti'], 'nelements': 2, 'material_id': 'mvc-13391'}}, {'type': 'structure', 'attributes': {'pretty_formula': 'TiO2', 'elements': ['O', 'Ti'], 'nelements': 2, 'material_id': 'mvc-12404'}}, {'type': 'structure', 'attributes': {'pretty_formula': 'TiO2', 'elements': ['O', 'Ti'], 'nelements': 2, 'material_id': 'mp-636827'}}, {'type': 'structure', 'attributes': {'pretty_formula': 'Ti3O2', 'elements': ['O', 'Ti'], 'nelements': 2, 'material_id': 'mp-978968'}}, {'type': 'structure', 'attributes': {'pretty_formula': 'Ti10O11', 'elements': ['O', 'Ti'], 'nelements': 2, 'material_id': 'mp-684733'}}, {'type': 'structure', 'attributes': {'pretty_formula': 'TiO2', 'elements': ['O', 'Ti'], 'nelements': 2, 'material_id': 'mvc-4715'}}]})
