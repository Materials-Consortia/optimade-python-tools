# pylint: disable=relative-beyond-top-level
import unittest

from .utils import SetClient


class CORSMiddlewareTest(SetClient, unittest.TestCase):

    server = "regular"

    def test_regular_CORS_request(self):
        response = self.client.get("/info", headers={"Origin": "http://example.org"})
        self.assertIn(
            ("access-control-allow-origin", "*"),
            tuple(response.headers.items()),
            msg=f"Access-Control-Allow-Origin header not found in response headers: {response.headers}",
        )

    def test_preflight_CORS_request(self):
        headers = {
            "Origin": "http://example.org",
            "Access-Control-Request-Method": "GET",
        }
        response = self.client.options("/info", headers=headers)
        for response_header in (
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
        ):
            self.assertIn(
                response_header.lower(),
                list(response.headers.keys()),
                msg=f"{response_header} header not found in response headers: {response.headers}",
            )


class IndexCORSMiddlewareTest(SetClient, unittest.TestCase):

    server = "index"

    def test_regular_CORS_request(self):
        response = self.client.get("/info", headers={"Origin": "http://example.org"})
        self.assertIn(
            ("access-control-allow-origin", "*"),
            tuple(response.headers.items()),
            msg=f"Access-Control-Allow-Origin header not found in response headers: {response.headers}",
        )

    def test_preflight_CORS_request(self):
        headers = {
            "Origin": "http://example.org",
            "Access-Control-Request-Method": "GET",
        }
        response = self.client.options("/info", headers=headers)
        for response_header in (
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
        ):
            self.assertIn(
                response_header.lower(),
                list(response.headers.keys()),
                msg=f"{response_header} header not found in response headers: {response.headers}",
            )
