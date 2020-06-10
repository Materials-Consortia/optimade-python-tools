# pylint: disable=relative-beyond-top-level,import-outside-toplevel
import unittest

from optimade.server.exceptions import BadRequest

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


class EnsureQueryParamIntegrityTest(SetClient, unittest.TestCase):

    server = "regular"

    def _check_error_response(
        self,
        request: str,
        expected_status: int = None,
        expected_title: str = None,
        expected_detail: str = None,
    ):
        expected_status = 400 if expected_status is None else expected_status
        expected_title = "Bad Request" if expected_title is None else expected_title
        super()._check_error_response(
            request, expected_status, expected_title, expected_detail
        )

    def test_wrong_html_form(self):
        """Using a parameter without equality sign `=` or values should result in a `400 Bad Request` response"""
        from optimade.server.query_params import EntryListingQueryParams

        for valid_query_parameter in EntryListingQueryParams().__dict__:
            request = f"/structures?{valid_query_parameter}"
            with self.assertRaises(BadRequest):
                self._check_error_response(
                    request,
                    expected_detail="A query parameter without an equal sign (=) is not supported by this server",
                )

    def test_wrong_html_form_one_wrong(self):
        """Using a parameter without equality sign `=` or values should result in a `400 Bad Request` response

        This should hold true, no matter the chosen (valid) parameter separator (either & or ;).
        """
        request = "/structures?filter&include=;response_format=json"
        with self.assertRaises(BadRequest):
            self._check_error_response(
                request,
                expected_detail="A query parameter without an equal sign (=) is not supported by this server",
            )

    def test_parameter_separation(self):
        """No matter the chosen (valid) parameter separator (either & or ;) the parameters should be split correctly"""
        from optimade.server.middleware import EnsureQueryParamIntegrity

        query_part = 'filter=id="mpf_1"&include=;response_format=json'
        expected_result = {'filter=id="mpf_1"', "include=", "response_format=json"}

        parsed_set_of_queries = EnsureQueryParamIntegrity(self.client.app).check_url(
            query_part
        )
        self.assertSetEqual(expected_result, parsed_set_of_queries)

    def test_empy_parameters(self):
        """If parameter separators are present, the middleware should still succeed"""
        from optimade.server.middleware import EnsureQueryParamIntegrity

        query_part = ";;&&;&"
        expected_result = {""}

        parsed_set_of_queries = EnsureQueryParamIntegrity(self.client.app).check_url(
            query_part
        )
        self.assertSetEqual(expected_result, parsed_set_of_queries)
