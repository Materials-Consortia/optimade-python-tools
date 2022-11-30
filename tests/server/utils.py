import json
import re
import warnings
from typing import Iterable, Optional, Type, Union
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from requests import Response
from starlette import testclient

import optimade.models.jsonapi as jsonapi
from optimade import __api_version__
from optimade.models import ResponseMeta


class OptimadeTestClient(TestClient):
    """Special OPTIMADE edition of FastAPI's (Starlette's) TestClient

    This is needed, since `urllib.parse.urljoin` removes paths from the passed
    `base_url`.
    So this will prepend any requests with the passed `version`.
    """

    def __init__(
        self,
        app: Union[testclient.ASGI2App, testclient.ASGI3App],
        base_url: str = "http://example.org",
        raise_server_exceptions: bool = True,
        root_path: str = "",
        version: str = "",
    ) -> None:
        super(OptimadeTestClient, self).__init__(
            app=app,
            base_url=base_url,
            raise_server_exceptions=raise_server_exceptions,
            root_path=root_path,
        )
        if version:
            if not version.startswith("v") and not version.startswith("/v"):
                version = f"/v{version}"
            if version.startswith("v"):
                version = f"/{version}"
            if re.match(r"/v[0-9](.[0-9]){0,2}", version) is None:
                warnings.warn(
                    f"Invalid version passed to client: {version!r}. "
                    f"Will use the default: '/v{__api_version__.split('.')[0]}'"
                )
                version = f"/v{__api_version__.split('.')[0]}"
        self.version = version

    def request(  # pylint: disable=too-many-locals
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> Response:
        if (
            re.match(r"/?v[0-9](.[0-9]){0,2}/", url) is None
            and not urlparse(url).scheme
        ):
            while url.startswith("/"):
                url = url[1:]
            url = f"{self.version}/{url}"
        return super(OptimadeTestClient, self).request(
            method=method,
            url=url,
            **kwargs,
        )


class BaseEndpointTests:
    """Base class for common tests of endpoints"""

    request_str: Optional[str] = None
    response_cls: Optional[Type[jsonapi.Response]] = None

    response: Optional[Response] = None
    json_response: Optional[dict] = None

    @staticmethod
    def check_keys(keys: list, response_subset: Iterable):
        for key in keys:
            assert (
                key in response_subset
            ), f"{key!r} missing from response {response_subset}"

    def test_response_okay(self):
        """Make sure the response was successful"""
        assert self.response.status_code == 200, (
            f"Request to {self.request_str} failed: "
            f"{json.dumps(self.json_response, indent=2)}"
        )

    def test_meta_response(self):
        """General test for `meta` property in response"""
        assert "meta" in self.json_response
        meta_required_keys = ResponseMeta.schema()["required"]
        meta_optional_keys = list(
            set(ResponseMeta.schema()["properties"].keys()) - set(meta_required_keys)
        )
        implemented_optional_keys = [
            "time_stamp",
            "data_returned",
            "provider",
            "data_available",
            "implementation",
            "schema",
            # TODO: These keys are not implemented in the example server implementations
            # Add them in when they are.
            # "last_id",
            # "response_message",
            # "warnings",
        ]

        self.check_keys(meta_required_keys, self.json_response["meta"])
        self.check_keys(implemented_optional_keys, meta_optional_keys)
        self.check_keys(implemented_optional_keys, self.json_response["meta"])

    def test_serialize_response(self):
        assert self.response_cls is not None, "Response class unset for this endpoint"
        self.response_cls(**self.json_response)  # pylint: disable=not-callable


class EndpointTests(BaseEndpointTests):
    """Run tests for an endpoint for both servers"""

    @pytest.fixture(autouse=True)
    def get_response(self, both_clients):
        self.response = both_clients.get(self.request_str)
        self.json_response = self.response.json()
        yield
        self.response = None
        self.json_response = None


class RegularEndpointTests(BaseEndpointTests):
    """Run tests for an endpoint, but _only_ for the regular server"""

    @pytest.fixture(autouse=True)
    def get_response(self, client):
        self.response = client.get(self.request_str)
        self.json_response = self.response.json()
        yield
        self.response = None
        self.json_response = None


class IndexEndpointTests(BaseEndpointTests):
    """Run tests for an endpoint, but _only_ for the index server"""

    @pytest.fixture(autouse=True)
    def get_response(self, index_client):
        self.response = index_client.get(self.request_str)
        self.json_response = self.response.json()
        yield
        self.response = None
        self.json_response = None


def client_factory():
    """Return TestClient for OPTIMADE server"""

    def inner(
        version: Optional[str] = None,
        server: str = "regular",
        raise_server_exceptions: bool = True,
        add_empty_endpoint: bool = False,
    ) -> OptimadeTestClient:
        """Create a test client for the reference servers parameterised by:

        - `version` (to be prepended to all requests),
        - `server` type ("regular" or "index"),
        - whether to raise exceptions from the server to the client
          (`raise_server_exceptions`),
        - whether to create an endpoint that returns an empty response
          at `/extensions/test_empty_body` used for testing streaming
          responses (`add_empty_endpoint`)

        """
        import importlib

        module_name = "optimade.server.main"
        if server == "index":
            module_name += "_index"
        server_module = importlib.import_module(module_name)
        app = server_module.app
        server_module.add_major_version_base_url(app)
        server_module.add_optional_versioned_base_urls(app)

        if add_empty_endpoint:

            from fastapi import APIRouter
            from fastapi.responses import PlainTextResponse
            from starlette.routing import Route

            async def empty(_):
                return PlainTextResponse(b"", 200)

            empty_router = APIRouter(
                routes=[Route("/extensions/test_empty_body", endpoint=empty)]
            )
            app.include_router(empty_router)

        if version:
            return OptimadeTestClient(
                app,
                base_url="http://example.org",
                version=version,
                raise_server_exceptions=raise_server_exceptions,
            )
        return OptimadeTestClient(
            app,
            base_url="http://example.org",
            raise_server_exceptions=raise_server_exceptions,
        )

    return inner


class NoJsonEndpointTests:
    """A simplified mixin class for tests on non-JSON endpoints."""

    request_str: Optional[str] = None
    response_cls: Optional[Type] = None

    response: Optional[Response] = None

    @pytest.fixture(autouse=True)
    def get_response(self, both_clients):
        """Get response from client"""
        self.response = both_clients.get(self.request_str)
        yield
        self.response = None

    def test_response_okay(self):
        """Make sure the response was successful"""
        assert (
            self.response.status_code == 200
        ), f"Request to {self.request_str} failed: {self.response.content}"
