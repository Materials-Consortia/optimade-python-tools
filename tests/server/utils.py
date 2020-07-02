# pylint: disable=import-outside-toplevel,no-name-in-module
import abc
from typing import Dict

from pydantic import BaseModel

from fastapi.testclient import TestClient

from optimade import __api_version__

VERSION_PREFIX = f"/v{__api_version__.split('.')[0]}"


def get_regular_client() -> TestClient:
    """Return TestClient for regular OPTIMADE server"""
    from optimade.server.main import app
    from optimade.server.routers import info, links, references, structures

    for endpoint in (info, links, references, structures):
        app.include_router(endpoint.router, prefix=VERSION_PREFIX)
    # need to explicitly set base_url, as the default "http://testserver"
    # does not validate as pydantic AnyUrl model
    return TestClient(app, base_url=f"http://example.org{VERSION_PREFIX}")


def get_index_client() -> TestClient:
    """Return TestClient for index meta-database OPTIMADE server"""
    from optimade.server.main_index import app
    from optimade.server.routers import index_info, links

    app.include_router(index_info.router, prefix=VERSION_PREFIX)
    app.include_router(links.router, prefix=VERSION_PREFIX)
    # need to explicitly set base_url, as the default "http://testserver"
    # does not validate as pydantic UrlStr model
    return TestClient(app, base_url=f"http://example.org{VERSION_PREFIX}")


class SetClient(abc.ABC):
    """Metaclass to instantiate the TestClients once"""

    server: str = None
    _client: Dict[str, TestClient] = {
        "index": get_index_client(),
        "regular": get_regular_client(),
    }

    @property
    def client(self) -> TestClient:
        exception_message = "Test classes using EndpointTestsMixin MUST specify a `server` attribute with a value that is either 'regular' or 'index'"
        if not hasattr(self, "server"):
            raise AttributeError(exception_message)
        if self.server in self._client:
            return self._client[self.server]
        raise ValueError(exception_message)

    # pylint: disable=no-member
    def _check_error_response(
        self,
        request: str,
        expected_status: int = None,
        expected_title: str = None,
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


class EndpointTestsMixin(SetClient):
    """ Mixin "base" class for common tests between endpoints. """

    server: str = "regular"
    request_str: str = None
    response_cls: BaseModel = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        meta_optional_keys = ["data_available", "implementation"]

        self.check_keys(meta_required_keys, self.json_response["meta"])
        self.check_keys(meta_optional_keys, self.json_response["meta"])

    def test_serialize_response(self):
        self.assertTrue(
            self.response_cls is not None, msg="Response class unset for this endpoint"
        )
        self.response_cls(**self.json_response)  # pylint: disable=not-callable

    def check_keys(self, keys: list, response_subset: dict):
        for key in keys:
            self.assertTrue(
                key in response_subset,
                msg="{} missing from response {}".format(key, response_subset),
            )


class SimpleEndpointTestsMixin(SetClient):
    """ A simplified mixin class for tests on non-JSON endpoints. """

    server: str = "regular"
    request_str: str = None
    response_cls = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.response = self.client.get(self.request_str)
        self.assertEqual(
            self.response.status_code,
            200,
            msg=f"Request failed: {self.response.content}",
        )
