"""Tests specifically for optimade.servers.routers.utils."""
from typing import Mapping, Optional, Tuple, Union
from unittest import mock

from requests.exceptions import ConnectionError

import pytest


def mocked_providers_list_response(
    url: Union[str, bytes] = "",
    param: Optional[Union[Mapping[str, str], Tuple[str, str]]] = None,
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
        def __init__(self, data: Union[list, dict], status_code: int):
            self.data = data
            self.status_code = status_code

        def json(self) -> Union[list, dict]:
            return self.data

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


def test_get_providers_warning(caplog, top_dir):
    """Make sure a warning is logged as a last resort."""
    from optimade.server.routers.utils import get_providers

    providers_symlink = top_dir.joinpath("optimade/server/data/providers.json")
    provider_list_urls = [
        "https://providers.optimade.org/v1/links",
        "https://raw.githubusercontent.com/Materials-Consortia/providers"
        "/master/src/links/v1/providers.json",
    ]

    try:
        if providers_symlink.exists():
            providers_symlink.rename(
                top_dir.joinpath("optimade/server/data/providers_test.json")
            )

        list_of_data_files = [_.name for _ in providers_symlink.parent.glob("*")]
        assert "providers.json" not in list_of_data_files
        assert "providers_test.json" in list_of_data_files

        caplog.clear()
        with mock.patch("requests.get", side_effect=ConnectionError):
            assert get_providers() == []

            warning_message = """Could not retrieve a list of providers!

    Tried the following resources:

{}
    The list of providers will not be included in the `/links`-endpoint.
""".format(
                "".join([f"    * {_}\n" for _ in provider_list_urls])
            )
            assert warning_message in caplog.messages

    finally:
        providers_symlink_test = top_dir.joinpath(
            "optimade/server/data/providers_test.json"
        )
        if providers_symlink_test.exists():
            providers_symlink_test.rename(
                top_dir.joinpath("optimade/server/data/providers.json")
            )

        list_of_data_files = [_.name for _ in providers_symlink_test.parent.glob("*")]
        assert "providers.json" in list_of_data_files
        assert "providers_test.json" not in list_of_data_files
