import requests

from unittest import TestCase

class OptimadeTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://127.0.0.1:5000"
    def test_structures_arg_parse(self):
        argument = f"{self.base_url}/structures/?elements=Au&nelements=3"
        print(argument)
        rv = requests.get(argument)
        self.assertEqual(rv.json(), {
  "elements": "Au",
  "nelements": 3
})
