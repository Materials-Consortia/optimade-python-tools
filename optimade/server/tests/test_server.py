from starlette.testclient import TestClient

from optimade.server.main import app

client = TestClient(app)

PREFIX = ""  # E.g. '', 'optimade/', 'optimade/v0.9', etc.


def test_info_endpoint():
    client.get("/info")


def test_info_structures_endpoint():
    client.get("/info/structures")


def test_structures_endpoint():
    client.get("/structures")


def test_single_structure_endpoint():
    client.get("/structures/0")
