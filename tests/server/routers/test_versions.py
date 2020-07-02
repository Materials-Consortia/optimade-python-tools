import unittest

from optimade import __api_version__
from ..utils import SimpleEndpointTestsMixin


class VersionsEndpointTests(SimpleEndpointTestsMixin, unittest.TestCase):

    request_str = "/versions"
    response_cls = str

    def test_versions_endpoint(self):
        self.assertEqual(
            self.response.text,
            f"version\n{__api_version__.replace('v', '').split('.')[0]}",
        )
        self.assertEqual(self.response.headers.get("header"), "present")
        self.assertTrue("text/csv" in self.response.headers.get("content-type"))
