import requests
from urlGenerator import generate
from unittest import TestCase
import pytest

class OptimadeTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://127.0.0.1:5000/optimade/0.9.6"
        cls.entry_point = "/structures"
    ### THIS IS NOT WORKING YET ###

    def test_required_fields_exist(self):
        params = {
            "filter": "nelements<3",
            "response_format": "jsonapi",
            "email_address": "dwinston@lbl.gov",
            "response_limit": "5",
            "response_fields": "id,nelements,material_id,elements,formula_prototype",
            "sort": "-nelements",
        }
        argument = generate(self.base_url,self.entry_point ,params)
        rv = requests.get(argument)
        response = rv.json()['response']
        self.assertEqual(('data' in response) and \
                         ('links' in response) and \
                         ('meta' in response), True)
