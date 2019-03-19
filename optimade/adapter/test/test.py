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
            "response_limit": "5",
            "response_fields": "id,nelements,material_id,elements,formula_prototype",
            "sort": "-nelements",
        }
        argument = generate(self.endpoint, params)
        rv = requests.get(argument)
        self.assertEqual(rv.json()['response'], {'data': [{'attributes': {'elements': ['O', 'Ti'],
                          'material_id': 'mp-775938',
                          'nelements': 2,
                          'pretty_formula': 'TiO2'},
           'type': 'structure'},
          {'attributes': {'elements': ['O', 'Ti'],
                          'material_id': 'mp-766454',
                          'nelements': 2,
                          'pretty_formula': 'TiO2'},
           'type': 'structure'},
          {'attributes': {'elements': ['O', 'Ti'],
                          'material_id': 'mp-9173',
                          'nelements': 2,
                          'pretty_formula': 'TiO2'},
           'type': 'structure'},
          {'attributes': {'elements': ['O', 'Ti'],
                          'material_id': 'mp-882',
                          'nelements': 2,
                          'pretty_formula': 'Ti6O'},
           'type': 'structure'},
          {'attributes': {'elements': ['O', 'Ti'],
                          'material_id': 'mvc-13391',
                          'nelements': 2,
                          'pretty_formula': 'TiO2'},
           'type': 'structure'}],
 'link': {'base_url': {'href': 'http://127.0.0.1:5000/optimade/0.9.6/',
                       'meta': {'version': '0.9.6'}},
          'next': None},
 'meta': {'api_version': '0.9.6',
          'data_available': 98,
          'data_returned': 5,
          'last_id': 'mvc-13391',
          'more_data_available': True,
          'query': {'representation': 'structures/?filter=nelements<3&response_format=jsonapi&email_address=dwinston%40lbl.gov&response_limit=5&response_fields=id%2Cnelements%2Cmaterial_id%2Celements%2Cformula_prototype&sort=-nelements'},
          'response_message': 'NOT IMPLEMENTED YET',
          'time_stamp': '2019-03-13T23:32:30.442353'}})
