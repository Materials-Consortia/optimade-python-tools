# pylint: disable=no-member,wrong-import-position
import unittest
import abc

from starlette.testclient import TestClient

from optimade.validator import ImplementationValidator

from optimade.models import IndexInfoResponse, LinksResponse

from optimade.server.main_index import app
from optimade.server.routers import index_info, links

# We need to remove the /optimade prefixes in order to have the tests run correctly.
app.include_router(index_info.router)
app.include_router(links.router)
# need to explicitly set base_url, as the default "http://testserver"
# does not validate as pydantic UrlStr model
CLIENT = TestClient(app, base_url="http://example.org/index/optimade")


class IndexEndpointTests(abc.ABC):
    """ Abstract base class for common tests between endpoints. """

    request_str = None
    response_cls = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client = CLIENT

        self.response = self.client.get(self.request_str)
        self.json_response = self.response.json()
        self.assertEqual(
            self.response.status_code,
            200,
            msg=f"Request failed: {self.response.json()}",
        )

    def test_meta_response(self):
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
        self.assertTrue(
            self.response_cls is not None, msg="Response class unset for this endpoint"
        )
        self.response_cls(**self.json_response)  # pylint: disable=not-callable

    def check_keys(self, keys, response_subset):
        for key in keys:
            self.assertTrue(
                key in response_subset,
                msg="{} missing from response {}".format(key, response_subset),
            )


class IndexInfoEndpointTests(IndexEndpointTests, unittest.TestCase):

    request_str = "/info"
    response_cls = IndexInfoResponse

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
            "is_index",
        ]
        self.check_keys(attributes, self.json_response["data"]["attributes"])
        self.assertTrue("relationships" in self.json_response["data"])
        relationships = ["default"]
        self.check_keys(relationships, self.json_response["data"]["relationships"])
        self.assertTrue(len(self.json_response["data"]["relationships"]["default"]), 1)


class LinksEndpointTests(IndexEndpointTests, unittest.TestCase):
    request_str = "/links"
    response_cls = LinksResponse


class ServerTestWithValidator(unittest.TestCase):
    def test_with_validator(self):
        validator = ImplementationValidator(client=CLIENT, index=True)
        validator.main()
        self.assertTrue(validator.valid)
