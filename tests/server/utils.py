# pylint: disable=import-outside-toplevel,no-name-in-module
import abc
from typing import Dict

from pydantic import BaseModel

from starlette.testclient import TestClient


def get_regular_client() -> TestClient:
    """Return TestClient for regular OPTiMaDe server"""
    from optimade.server.main import app
    from optimade.server.routers import info, links, references, structures

    # We need to remove the /optimade prefixes in order to have the tests run correctly.
    app.include_router(info.router)
    app.include_router(links.router)
    app.include_router(references.router)
    app.include_router(structures.router)
    # need to explicitly set base_url, as the default "http://testserver"
    # does not validate as pydantic AnyUrl model
    return TestClient(app, base_url="http://example.org/optimade/v0")


def get_index_client() -> TestClient:
    """Return TestClient for index meta-database OPTiMaDe server"""
    from optimade.server.main_index import app
    from optimade.server.routers import index_info, links

    # We need to remove the /optimade prefixes in order to have the tests run correctly.
    app.include_router(index_info.router)
    app.include_router(links.router)
    # need to explicitly set base_url, as the default "http://testserver"
    # does not validate as pydantic UrlStr model
    return TestClient(app, base_url="http://example.org/optimade/v0")


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
