import dataclasses
import json
from typing import TYPE_CHECKING

import pytest

from optimade.validator import ImplementationValidator

if TYPE_CHECKING:
    from .utils import OptimadeTestClient

pytestmark = pytest.mark.filterwarnings("ignore")


def test_with_validator(both_fake_remote_clients: "OptimadeTestClient") -> None:
    from optimade.server.main_index import app

    validator = ImplementationValidator(
        client=both_fake_remote_clients,
        index=both_fake_remote_clients.app == app,
    )

    validator.validate_implementation()
    assert validator.valid


def test_with_validator_skip_optional(
    both_fake_remote_clients: "OptimadeTestClient",
) -> None:
    from optimade.server.main_index import app

    validator = ImplementationValidator(
        client=both_fake_remote_clients,
        index=both_fake_remote_clients.app == app,
        run_optional_tests=False,
    )

    validator.validate_implementation()
    assert validator.valid


def test_with_validator_json_response(
    both_fake_remote_clients: "OptimadeTestClient", capsys: pytest.CaptureFixture
) -> None:
    """Test that the validator writes compliant JSON when requested."""
    from optimade.server.main_index import app

    validator = ImplementationValidator(
        client=both_fake_remote_clients,
        index=both_fake_remote_clients.app == app,
        respond_json=True,
    )
    validator.validate_implementation()

    captured = capsys.readouterr()
    json_response = json.loads(captured.out)
    assert json_response["failure_count"] == 0, json_response
    assert json_response["internal_failure_count"] == 0, json_response
    assert json_response["optional_failure_count"] == 0, json_response
    assert validator.results.failure_count == 0, json_response
    assert validator.results.internal_failure_count == 0, json_response
    assert validator.results.optional_failure_count == 0, json_response
    assert dataclasses.asdict(validator.results) == json_response, json_response
    assert validator.valid


def test_with_validator_calculations(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that the validator handles an entry type without a dedicated model,
    by serving the reference server's `references` as `calculations` entries that
    only have the properties shared by all entry types.
    """
    from .utils import client_factory

    shared = ("id", "type", "immutable_id", "last_modified")

    def as_calculation(entry: dict) -> dict:
        attributes = {
            key: value
            for key, value in entry.get("attributes", {}).items()
            if key in shared
        }
        return {"id": entry["id"], "type": "calculations", "attributes": attributes}

    client = client_factory()(server="regular", raise_server_exceptions=False)
    get = client.get

    def get_with_calculations(url, *args, **kwargs):
        url = str(url)
        if url.startswith("calculations"):
            response = get("references" + url[len("calculations") :], *args, **kwargs)
            if response.status_code != 200:
                return response
            body = response.json()
            if isinstance(body["data"], list):
                body["data"] = [as_calculation(entry) for entry in body["data"]]
            else:
                body["data"] = as_calculation(body["data"])
        elif url == "info/calculations":
            response = get("info/references", *args, **kwargs)
            body = response.json()
            body["data"]["id"] = "calculations"
            body["data"]["properties"] = {
                name: prop
                for name, prop in body["data"]["properties"].items()
                if name in shared
            }
            body["data"]["output_fields_by_format"] = {"json": list(shared)}
        elif url == "info":
            response = get(url, *args, **kwargs)
            body = response.json()
            body["data"]["attributes"]["entry_types_by_format"]["json"].append(
                "calculations"
            )
            body["data"]["attributes"]["available_endpoints"].append("calculations")
        else:
            return get(url, *args, **kwargs)
        return type(response)(response.status_code, json=body, request=response.request)

    monkeypatch.setattr(client, "get", get_with_calculations)

    validator = ImplementationValidator(client=client)
    validator.validate_implementation()
    assert validator.results.failure_count == 0
    assert validator.results.internal_failure_count == 0
    assert validator.valid


def test_as_type_with_validator(
    client: "OptimadeTestClient", capsys: pytest.CaptureFixture
) -> None:
    from unittest.mock import Mock, patch

    test_urls = {
        f"{client.base_url}/structures": "structures",
        f"{client.base_url}/structures/mpf_1": "structure",
        f"{client.base_url}/references": "references",
        f"{client.base_url}/references/dijkstra1968": "reference",
        f"{client.base_url}/info": "info",
        f"{client.base_url}/links": "links",
    }
    with patch("requests.get", Mock(side_effect=client.get)):
        for url, as_type in test_urls.items():
            validator = ImplementationValidator(
                base_url=url, as_type=as_type, respond_json=True
            )
            validator.validate_implementation()
            assert validator.valid

            captured = capsys.readouterr()
            json_response = json.loads(captured.out)

            assert json_response["failure_count"] == 0
            assert json_response["internal_failure_count"] == 0
            assert json_response["optional_failure_count"] == 0
            assert validator.results.failure_count == 0
            assert validator.results.internal_failure_count == 0
            assert validator.results.optional_failure_count == 0
            assert dataclasses.asdict(validator.results) == json_response


def test_query_value_formatting() -> None:
    from optimade.models.optimade_json import DataType

    format_value_fn = ImplementationValidator._format_test_value

    assert format_value_fn(["Ag", "Ba", "Ca"], DataType.LIST, "HAS") == '"Ag"'
    assert (
        format_value_fn(["Ag", "Ba", "Ca"], DataType.LIST, "HAS ANY")
        == '"Ag","Ba","Ca"'
    )
    assert format_value_fn([6, 1, 4], DataType.LIST, "HAS ALL") == "1,4,6"
    assert format_value_fn("test value", DataType.STRING, "CONTAINS") == '"test value"'
    assert format_value_fn(5, DataType.INTEGER, "=") == 5


@pytest.mark.parametrize("server", ["regular", "index"])
def test_versioned_base_urls(
    client: "OptimadeTestClient", index_client: "OptimadeTestClient", server: str
) -> None:
    """Test all expected versioned base URLs responds with 200

    This depends on the routers for each kind of server.
    """

    from optimade.server.routers.utils import BASE_URL_PREFIXES

    clients = {
        "regular": client,
        "index": index_client,
    }

    valid_endpoints = {
        "regular": ("/info", "/links", "/references", "/structures"),
        "index": ("/info", "/links"),
    }

    for version in BASE_URL_PREFIXES.values():
        for endpoint in valid_endpoints[server]:
            response = clients[server].get(url=version + endpoint)
            json_response = response.json()

            assert response.status_code == 200, (
                f"Request to {response.url} failed for server {server!r}: "
                f"{json.dumps(json_response, indent=2)}"
            )
            assert "meta" in json_response, (
                f"Mandatory 'meta' top-level field not found in request to {response.url} for "
                f"server {server!r}. Response: {json.dumps(json_response, indent=2)}"
            )


@pytest.mark.parametrize("server", ["regular", "index"])
def test_meta_schema_value_obeys_index(
    client: "OptimadeTestClient", index_client: "OptimadeTestClient", server: str
) -> None:
    """Test that the reported `meta->schema` is correct for index/non-index
    servers.
    """

    from optimade.server.config import ServerConfig
    from optimade.server.routers.utils import BASE_URL_PREFIXES

    config = ServerConfig()

    clients = {
        "regular": client,
        "index": index_client,
    }

    for version in BASE_URL_PREFIXES.values():
        # Mimic the effect of the relevant server's startup
        config.is_index = server == "index"
        response = clients[server].get(url=version + "/links")
        json_response = response.json()

        assert response.status_code == 200, (
            f"Request to {response.url} failed for server {server!r}: "
            f"{json.dumps(json_response, indent=2)}"
        )
        assert "meta" in json_response, (
            f"Mandatory 'meta' top-level field not found in request to {response.url} for "
            f"server {server!r}. Response: {json.dumps(json_response, indent=2)}"
        )

        if server == "regular":
            assert json_response["meta"].get("schema") == config.schema_url
        else:
            assert json_response["meta"].get("schema") == config.index_schema_url
