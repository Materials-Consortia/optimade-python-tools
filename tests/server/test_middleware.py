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
        request,
        expected_status: int = 400,
        expected_title: str = "Bad Request",
        expected_detail: str = None,
    ):
        try:
            response = self.client.get(request)
            self.assertEqual(
                response.status_code,
                expected_status,
                msg=f"Request should have been an error with status code {expected_status}, "
                f"but instead {response.status_code} was received.\nResponse:\n{response.json()}",
            )
            response = response.json()
            self.assertEqual(len(response["errors"]), 1)
            self.assertEqual(response["meta"]["data_returned"], 0)

            error = response["errors"][0]
            self.assertEqual(str(expected_status), error["status"])
            self.assertEqual(expected_title, error["title"])

            if expected_detail is None:
                expected_detail = "Error trying to process rule "
                self.assertTrue(error["detail"].startswith(expected_detail))
            else:
                self.assertEqual(expected_detail, error["detail"])

        except Exception as exc:
            print("Request attempted:")
            print(f"{self.client.base_url}{request}")
            raise exc

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
        request = f"/structures?filter&include=;response_format=json"
        with self.assertRaises(BadRequest):
            self._check_error_response(
                request,
                expected_detail="A query parameter without an equal sign (=) is not supported by this server",
            )

    def test_parameter_separation(self):
        """No matter the chosen (valid) parameter separator (either & or ;) the parameters should be split correctly"""
        from optimade.server.middleware import EnsureQueryParamIntegrity

        query_part = 'filter=""&include=;response_format=json'
        expected_result = {'filter=""', "include=", "response_format=json"}

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
