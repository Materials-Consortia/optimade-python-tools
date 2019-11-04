import unittest
import abc

from starlette.testclient import TestClient

from optimade.server.config import CONFIG

CONFIG.page_limit = 5

from optimade.server.main import app
from optimade.models import (
    StructureResponseMany,
    StructureResponseOne,
    EntryInfoResponse,
    InfoResponse,
)


class EndpointTests(abc.ABC):
    """ Abstract base class for common tests between endpoints. """

    request_str = None
    response_cls = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # need to explicitly set base_url as the default "http://testserver"
        # does not validate as pydantic UrlStr model
        self.client = TestClient(app, base_url="http://example.org/optimade")

        self.response = self.client.get(self.request_str)
        self.json_response = self.response.json()
        self.assertEqual(
            self.response.status_code,
            200,
            msg=f"Request failed: {self.response.json()}",
        )

    def test_meta_reponse(self):
        self.assertTrue("meta" in self.json_response)
        meta_required_keys = [
            "query",
            "api_version",
            "time_stamp",
            "data_returned",
            "more_data_available",
            "provider",
        ]

        self.check_keys(meta_required_keys, self.json_response["meta"])

    def test_serialize_response(self):
        self.response_cls(**self.json_response)

    def check_keys(self, keys, response_subset):
        for key in keys:
            self.assertTrue(
                key in response_subset,
                msg="{} missing from response".format(key, response_subset),
            )


class InfoEndpointTests(EndpointTests, unittest.TestCase):

    request_str = "/info"
    response_cls = InfoResponse

    def test_info_endpoint_attributes(self):
        self.assertTrue("data" in self.json_response)
        self.assertEqual(self.json_response["data"]["type"], "info")
        self.assertEqual(self.json_response["data"]["id"], "/")
        self.assertTrue("attributes" in self.json_response["data"])
        attributes = [
            "api_version",
            "available_api_versions",
            "formats",
            "entry_types_by_format",
            "available_endpoints",
        ]
        self.check_keys(attributes, self.json_response["data"]["attributes"])


class InfoStructuresEndpointTests(EndpointTests, unittest.TestCase):

    request_str = "/info/structures"
    response_cls = EntryInfoResponse

    def test_info_structures_endpoint_data(self):
        self.assertTrue("data" in self.json_response)
        data_keys = ["description", "properties", "formats", "output_fields_by_format"]
        self.check_keys(data_keys, self.json_response["data"])


class StructuresEndpointTests(EndpointTests, unittest.TestCase):

    request_str = "/structures"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        self.assertTrue("data" in self.json_response)
        self.assertEqual(len(self.json_response["data"]), 5)
        self.assertTrue("meta" in self.json_response)
        self.assertEqual(self.json_response["meta"]["data_available"], 17)
        self.assertEqual(self.json_response["meta"]["more_data_available"], True)

    def test_get_next_responses(self):
        cursor = self.json_response["data"]
        more_data_available = True
        next_request = self.json_response["links"]["next"]

        while more_data_available:
            next_response = self.client.get(next_request).json()
            next_request = next_response["links"]["next"]
            cursor.extend(next_response["data"])
            more_data_available = next_response["meta"]["more_data_available"]
            if more_data_available:
                self.assertEqual(len(next_response["data"]), 5)
            else:
                self.assertEqual(len(next_response["data"]), 2)

        self.assertEqual(len(cursor), 17)


class SingleStructureEndpointTests(EndpointTests, unittest.TestCase):

    test_id = "mpf_1"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        self.assertTrue("data" in self.json_response)
        self.assertEqual(self.json_response["data"]["id"], self.test_id)
        self.assertEqual(self.json_response["data"]["type"], "structures")
        self.assertTrue("attributes" in self.json_response["data"])
        self.assertTrue(
            "_exmpl__mp_chemsys" in self.json_response["data"]["attributes"]
        )
