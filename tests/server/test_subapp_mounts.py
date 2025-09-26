# test_subapp_mounts.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from optimade.server.config import ServerConfig
from optimade.server.create_app import create_app

CONFIG = ServerConfig()


@pytest.fixture
def mounted_client():
    """Mount 3 Optimade APIs with different Mongo databases."""
    parent_app = FastAPI()

    base_url = "http://testserver"

    conf1 = ServerConfig()
    conf1.base_url = f"{base_url}/app1"
    conf1.mongo_database = "optimade_1"
    conf1.provider = {
        "name": "Example 1",
        "description": "Example 1",
        "prefix": "example1",
    }
    app1 = create_app(conf1)
    parent_app.mount("/app1", app1)

    conf2 = ServerConfig()
    conf2.base_url = f"{base_url}/app2"
    conf2.mongo_database = "optimade_2"
    conf2.provider = {
        "name": "Example 2",
        "description": "Example 2",
        "prefix": "example2",
    }
    app2 = create_app(conf2)
    parent_app.mount("/app2", app2)

    conf3 = ServerConfig()
    conf3.base_url = f"{base_url}/idx"
    conf3.mongo_database = "optimade_idx"
    app3 = create_app(conf3, index=True)
    parent_app.mount("/idx", app3)

    return TestClient(parent_app)


@pytest.mark.skipif(
    CONFIG.database_backend.value not in ("mongomock", "mongodb"),
    reason="Requires db-specific config, only MongoDB currently supported.",
)
def test_subapps(mounted_client):
    for app in ["app1", "app2"]:
        r = mounted_client.get(f"/{app}/structures")
        assert r.status_code == 200, f"API not reachable for /{app}"
        response = r.json()
        # Make sure we get at least 10 structures:
        assert len(response["data"]) > 10

        # Make sure the custom providers were picked up:
        prefix = response["meta"]["provider"]["prefix"]
        if app == "app1":
            assert prefix == "example1"
        if app == "app2":
            assert prefix == "example2"

    # the index, make sure links are accessible
    r = mounted_client.get("/idx/links")
    assert r.status_code == 200, "API not reachable for /idx"
    response = r.json()
    assert len(response["data"]) > 5
