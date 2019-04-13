import requests
import datetime
import dateutil.parser
from urlGenerator import generate
from unittest import TestCase
import pytest

class OptimadeTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://127.0.0.1:5000/optimade/0.9.6"
        cls.entry_point = "/structures"
        cls.general_params = {
            "filter": "nelements<3",
            "response_format": "jsonapi",
            "email_address": "dwinston@lbl.gov",
            "response_limit": 5,
            "response_fields": "nelements,material_id,elements,formula_prototype",
            "sort": "-nelements",
            "page": 5
        }
        cls.general_response = requests.get(generate(cls.base_url,cls.entry_point ,cls.general_params)).json()['response']

    def testDataFieldExist(self):
        self.assertIn("data", self.general_response)
    def testLinksFieldExist(self):
        self.assertIn("links", self.general_response)
    def testMetaFieldExist(self):
        self.assertIn("meta", self.general_response)

    ######## Test Meta Fields ########
    def testApiversion(self):
        self.assertIn("api_version",self.general_response["meta"])
        self.assertEqual("0.9.6", self.general_response["meta"]["api_version"])
    def testDataAvailable(self):
        self.assertIn("data_available",self.general_response["meta"])
        self.assertEqual(20522, self.general_response["meta"]["data_available"])
    def testDataReturned(self):
        self.assertIn("data_returned",self.general_response["meta"])
        self.assertEqual(5, self.general_response["meta"]["data_returned"])
    def testLastId(self):
        self.assertIn("last_id",self.general_response["meta"])
        self.assertEqual("mp-151", self.general_response["meta"]["last_id"])
    def testMoreDataAvailable(self):
        self.assertIn("more_data_available",self.general_response["meta"])
        self.assertTrue(self.general_response["meta"]["more_data_available"])
    def testQuery(self):
        self.assertIn("query",self.general_response["meta"])
        self.assertIn("representation",self.general_response["meta"]["query"])
        # self.assertEqual("structures/?filter=nelements<3&response_format=jsonapi&email_address=dwinston%40lbl.gov&response_limit=5&response_fields=id%2Cnelements%2Cmaterial_id%2Celements%2Cformula_prototype&sort=-nelements&page=5",self.general_response["meta"]["query"]["representation"])
    def testTimeStamp(self):
        self.assertIn("time_stamp", self.general_response["meta"])
        current_time = datetime.datetime.now()
        self.assertTrue(datetime.datetime.now() - dateutil.parser.parse((self.general_response["meta"]["time_stamp"])) < datetime.timedelta(seconds=10))

    ######## Test links Fields ########
    def testBaseUrl(self):
        self.assertIn("base_url",self.general_response["links"])
        self.assertIn("href", self.general_response["links"]["base_url"])
        self.assertIn("meta", self.general_response["links"]["base_url"])
        self.assertEqual("http://127.0.0.1:5000/optimade/0.9.6/", self.general_response["links"]["base_url"]["href"])
        self.assertIn("version", self.general_response["links"]["base_url"]["meta"])
        self.assertEqual("0.9.6", self.general_response["links"]["base_url"]["meta"]["version"])
    def testFirst(self):
        self.assertIn("first",self.general_response["links"])
        # self.assertEqual("http://127.0.0.1:5000/optimade/0.9.6/structures/?filter=nelements%3C3&response_format=jsonapi&email_address=dwinston%40lbl.gov&response_limit=5&response_fields=id%2Cnelements%2Cmaterial_id%2Celements%2Cformula_prototype&sort=-nelements&page=1",self.general_response["links"]["first"])
    def testLast(self):
        self.assertIn("last",self.general_response["links"])
        # self.assertEqual("http://127.0.0.1:5000/optimade/0.9.6/structures/?filter=nelements%3C3&response_format=jsonapi&email_address=dwinston%40lbl.gov&response_limit=5&response_fields=id%2Cnelements%2Cmaterial_id%2Celements%2Cformula_prototype&sort=-nelements&page=4105",self.general_response["links"]["last"])
    def testPrev(self):
        self.assertIn("prev",self.general_response["links"])
        # self.assertEqual("http://127.0.0.1:5000/optimade/0.9.6/structures/?filter=nelements%3C3&response_format=jsonapi&email_address=dwinston%40lbl.gov&response_limit=5&response_fields=id%2Cnelements%2Cmaterial_id%2Celements%2Cformula_prototype&sort=-nelements&page=4",self.general_response["links"]["prev"])
    def testNext(self):
        self.assertIn("next",self.general_response["links"])
        # self.assertEqual("http://127.0.0.1:5000/optimade/0.9.6/structures/?filter=nelements%3C3&response_format=jsonapi&email_address=dwinston%40lbl.gov&response_limit=5&response_fields=id%2Cnelements%2Cmaterial_id%2Celements%2Cformula_prototype&sort=-nelements&page=6",self.general_response["links"]["next"])

    ######## Test data Fields ########
    def testDataAmountMatch(self):
        data = self.general_response["data"]
        self.assertTrue(len(data) == self.general_params["response_limit"])
    def testDataAmountMatch(self):
        data = self.general_response["data"]
        self.assertTrue(len(data) == self.general_params["response_limit"])

    ######## Error testing ########
    def testOtherReturnType(self):
        params = {
            "filter": "nelements<3",
            "response_format": "xml",
            "email_address": "dwinston@lbl.gov",
            "response_limit": 5,
            "response_fields": "nelements,material_id,elements,formula_prototype",
            "sort": "-nelements",
            "page": 5
        }
        response = requests.get(generate(self.base_url,self.entry_point ,params)).json()['response']
        self.assertIn("ERROR", response)
