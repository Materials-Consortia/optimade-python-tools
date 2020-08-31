import os
from traceback import print_exc

import pytest

from optimade.validator import ImplementationValidator


def test_with_validator(both_clients):
    from optimade.server.main_index import app

    validator = ImplementationValidator(
        client=both_clients,
        index=both_clients.app == app,
    )
    try:
        validator.main()
    except Exception:
        print_exc()
    assert validator.valid


def test_mongo_backend_package_used():
    import pymongo
    import mongomock
    from optimade.server.entry_collections import client

    force_mongo_env_var = os.environ.get("OPTIMADE_CI_FORCE_MONGO", None)
    if force_mongo_env_var is None:
        return

    if int(force_mongo_env_var) == 1:
        assert issubclass(client.__class__, pymongo.MongoClient)
    elif int(force_mongo_env_var) == 0:
        assert issubclass(client.__class__, mongomock.MongoClient)
    else:
        raise pytest.fail(
            "The environment variable OPTIMADE_CI_FORCE_MONGO cannot be parsed as an int."
        )


def test_as_type_with_validator(client):
    import unittest

    test_urls = {
        f"{client.base_url}/structures": "structures",
        f"{client.base_url}/structures/mpf_1": "structure",
        f"{client.base_url}/references": "references",
        f"{client.base_url}/references/dijkstra1968": "reference",
        f"{client.base_url}/info": "info",
        f"{client.base_url}/links": "links",
    }
    with unittest.mock.patch(
        "requests.get", unittest.mock.Mock(side_effect=client.get)
    ):
        for url, as_type in test_urls.items():
            validator = ImplementationValidator(
                base_url=url, as_type=as_type, verbosity=5
            )
            try:
                validator.main()
            except Exception:
                print_exc()
            assert validator.valid


@pytest.mark.parametrize("server", ["regular", "index"])
def test_versioned_base_urls(client, index_client, server: str):
    """Test all expected versioned base URLs responds with 200

    This depends on the routers for each kind of server.
    """
    try:
        import simplejson as json
    except ImportError:
        import json

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
