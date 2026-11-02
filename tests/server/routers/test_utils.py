"""Tests specifically for optimade.servers.routers.utils."""

from collections.abc import Mapping
from unittest import mock

import pytest
import requests
from requests.exceptions import ConnectionError, SSLError


class _MockResponse:
    def __init__(self, data: list | dict, status_code: int):
        self.data = data
        self.status_code = status_code

    def json(self) -> list | dict:
        return self.data

    @property
    def content(self) -> str:
        return str(self.data)


def mocked_providers_list_response(
    url: str | bytes = "",
    param: Mapping[str, str] | tuple[str, str] | None = None,
    **kwargs,
):
    """This function will be used to mock requests.get

    It will _always_ return a successful response, returning the submodule's provider.json.

    NOTE: This function is loosely inspired by the stackoverflow response here:
        https://stackoverflow.com/questions/15753390/how-can-i-mock-requests-and-the-response
    """
    try:
        from optimade.server.data import providers
    except ImportError:
        pytest.fail(
            "Cannot import providers from optimade.server.data, "
            "please initialize the `providers` submodule!"
        )

    class MockResponse:
        def __init__(self, data: list | dict, status_code: int):
            self.data = data
            self.status_code = status_code

        def json(self) -> list | dict:
            return self.data

        def content(self) -> str:
            return str(self.data)

    return MockResponse(providers, 200)


def test_get_providers():
    """Make sure valid responses are handled as expected."""
    try:
        from optimade.server.data import providers
    except ImportError:
        pytest.fail(
            "Cannot import providers from optimade.server.data, "
            "please initialize the `providers` submodule!"
        )

    from optimade.server.routers.utils import get_providers, mongo_id_for_database

    side_effects = [
        mocked_providers_list_response,
        ConnectionError,
    ]

    for side_effect in side_effects:
        with mock.patch("requests.get", side_effect=side_effect):
            providers_list = [
                _ for _ in providers.get("data", []) if _["id"] != "exmpl"
            ]
            for provider in providers_list:
                provider.update(
                    {
                        "_id": {
                            "$oid": mongo_id_for_database(
                                provider["id"], provider["type"]
                            )
                        }
                    }
                )
            assert get_providers() == providers_list


def test_get_all_databases():
    from optimade.utils import get_all_databases

    assert list(get_all_databases())


def test_get_providers_uses_provided_session():
    """A caller-supplied `requests.Session` must be used for the provider-list
    request, so custom HTTP config (e.g. proxies) is honoured.

    https://github.com/Materials-Consortia/optimade-python-tools/issues/2275
    """
    from optimade.utils import get_providers

    session = mock.MagicMock(spec=requests.Session)
    session.get.return_value = mocked_providers_list_response()

    # If the global `requests.get` is used instead of the session, this raises.
    with mock.patch(
        "requests.get", side_effect=AssertionError("used requests.get, not the session")
    ):
        providers_list = get_providers(session=session)

    assert session.get.called
    assert providers_list


def test_get_child_database_links_uses_provided_session():
    """`get_child_database_links` must route its request through a supplied session.

    https://github.com/Materials-Consortia/optimade-python-tools/issues/2275
    """
    from optimade.utils import get_child_database_links

    session = mock.MagicMock(spec=requests.Session)
    session.get.return_value = _MockResponse({"data": []}, 200)
    provider = {"id": "dummy", "base_url": "https://example.org"}

    with mock.patch(
        "requests.get", side_effect=AssertionError("used requests.get, not the session")
    ):
        links = get_child_database_links(provider, session=session)

    assert links == []
    assert session.get.called


def test_get_child_database_links_skip_ssl_uses_session():
    """On an SSL error with `skip_ssl=True`, the `verify=False` retry must also be
    routed through the supplied session.

    https://github.com/Materials-Consortia/optimade-python-tools/issues/2275
    """
    from optimade.utils import get_child_database_links

    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [SSLError("ssl boom"), _MockResponse({"data": []}, 200)]
    provider = {"id": "dummy", "base_url": "https://example.org"}

    with mock.patch(
        "requests.get", side_effect=AssertionError("used requests.get, not the session")
    ):
        links = get_child_database_links(provider, session=session, skip_ssl=True)

    assert links == []
    assert session.get.call_count == 2
    assert session.get.call_args.kwargs.get("verify") is False


def test_get_all_databases_threads_session():
    """`get_all_databases` must forward its session to the helper scrapers.

    https://github.com/Materials-Consortia/optimade-python-tools/issues/2275
    """
    from optimade import utils

    session = mock.MagicMock(spec=requests.Session)
    provider = {"id": "dummy", "base_url": "https://example.org"}

    with (
        mock.patch.object(
            utils, "get_providers", return_value=[provider]
        ) as mock_get_providers,
        mock.patch.object(
            utils, "get_child_database_links", return_value=[]
        ) as mock_get_links,
    ):
        list(utils.get_all_databases(session=session))

    assert mock_get_providers.call_args.kwargs.get("session") is session
    assert mock_get_links.call_args.kwargs.get("session") is session


def test_get_providers_warning(caplog, top_dir):
    """Make sure a warning is logged as a last resort."""
    import copy

    from optimade.server.routers.utils import PROVIDER_LIST_URLS, get_providers

    providers_cache = False
    try:
        from optimade.server import data

        if getattr(data, "providers", None) is not None:
            providers_cache = copy.deepcopy(data.providers)

        caplog.clear()
        with mock.patch("requests.get", side_effect=ConnectionError):
            del data.providers
            assert get_providers() == []

            warning_message = """Could not retrieve a list of providers!

    Tried the following resources:

{}
    The list of providers will not be included in the `/links`-endpoint.
""".format("".join([f"    * {_}\n" for _ in PROVIDER_LIST_URLS]))
            assert warning_message in caplog.messages

    finally:
        if providers_cache:
            from optimade.server import data

            data.providers = providers_cache

            # Trying to import providers to make sure it's there again now
            from optimade.server.data import providers

            assert providers == providers_cache


@pytest.mark.parametrize(
    "request_url,expected",
    [
        ("http://www.example.com", "http://www.example.com/optimade"),
        ("http://www.example.com/", "http://www.example.com/optimade"),
        ("http://www.example.com/optimade/v1/links", "http://www.example.com/optimade"),
        ("http://www.structures.com/links", "http://www.structures.com/optimade"),
        (
            "https://www.links.org/optimade/structures/123456",
            "https://www.links.org/optimade",
        ),
    ],
)
@pytest.mark.parametrize("root_path", ["/optimade", "/optimade/", "optimade"])
def test_get_base_url_with_root_path(request_url, expected, root_path):
    """Check that the configured `root_path` is included when the base URL
    is derived from the request URL."""
    from optimade.server.config import ServerConfig
    from optimade.server.routers.utils import get_base_url

    config = ServerConfig.model_construct(base_url=None, root_path=root_path)
    assert get_base_url(config, request_url) == expected


def test_get_base_url_without_root_path():
    """Check that the base URL is only the scheme and netloc when no
    `root_path` or `base_url` are configured."""
    from optimade.server.config import ServerConfig
    from optimade.server.routers.utils import get_base_url

    config = ServerConfig.model_construct(base_url=None, root_path=None)
    assert (
        get_base_url(config, "https://www.example.com/v1/structures")
        == "https://www.example.com"
    )


def test_get_base_url_config_takes_precedence():
    """Check that a configured `base_url` overrides `root_path` handling."""
    from optimade.server.config import ServerConfig
    from optimade.server.routers.utils import get_base_url

    config = ServerConfig.model_construct(
        base_url="https://example.org/api/", root_path="/optimade"
    )
    assert (
        get_base_url(config, "http://www.example.com/optimade/v1/links")
        == "https://example.org/api"
    )


def _make_request(url: str, root_path: str = ""):
    """Build a minimal Starlette request for the given URL and ASGI `root_path`."""
    import urllib.parse

    from starlette.requests import Request

    parsed = urllib.parse.urlsplit(url)
    return Request(
        {
            "type": "http",
            "scheme": parsed.scheme,
            "server": (parsed.hostname, parsed.port or 80),
            "path": parsed.path or "/",
            "root_path": root_path,
            "query_string": parsed.query.encode(),
            "headers": [(b"host", parsed.netloc.encode())],
        }
    )


@pytest.mark.parametrize(
    "scope_root_path,config_root_path,expected",
    [
        # Mounted sub-application: only the ASGI scope knows the prefix
        ("/app1", None, "http://www.example.com/app1"),
        # Scope takes precedence over config
        ("/app1", "/optimade", "http://www.example.com/app1"),
        # Empty scope root path falls back to config
        ("", "/optimade", "http://www.example.com/optimade"),
        ("", None, "http://www.example.com"),
    ],
)
def test_get_base_url_from_request_scope(scope_root_path, config_root_path, expected):
    """Check that the base URL includes the `root_path` from the request's ASGI
    scope, e.g., when the app is mounted as a sub-application."""
    from optimade.server.config import ServerConfig
    from optimade.server.routers.utils import get_base_url

    config = ServerConfig.model_construct(base_url=None, root_path=config_root_path)
    request = _make_request(
        f"http://www.example.com{scope_root_path}/v1/structures", scope_root_path
    )
    assert get_base_url(config, request) == expected


def test_get_base_url_explicit_root_path():
    """Check that an explicitly passed `root_path` overrides the config and scope."""
    from optimade.server.config import ServerConfig
    from optimade.server.routers.utils import get_base_url

    config = ServerConfig.model_construct(base_url=None, root_path="/optimade")
    request = _make_request("http://www.example.com/app1/v1/structures", "/app1")
    assert (
        get_base_url(config, request, root_path="/other")
        == "http://www.example.com/other"
    )
    assert (
        get_base_url(config, "http://www.example.com/x", root_path="/other/")
        == "http://www.example.com/other"
    )
