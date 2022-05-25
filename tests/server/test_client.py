from pathlib import Path
import json

import pytest
import httpx
from functools import partial
from pytest_httpx import HTTPXMock

from optimade.client import OptimadeClient
from optimade.client.cli import _get


TEST_URLS = [
    "https://example.com",
    "https://example.org",
    "https://optimade.herokuapp.com",
]
TEST_URL = TEST_URLS[0]


@pytest.fixture(scope="function")
def httpx_mocked_response(httpx_mock, client):
    def httpx_mock_response(client, request: httpx.Request):
        response = client.get(str(request.url))
        return httpx.Response(status_code=response.status_code, json=response.json())

    httpx_mock.add_callback(partial(httpx_mock_response, client))
    yield httpx_mock


@pytest.mark.parametrize("use_async", [False])
def test_client_endpoints(httpx_mocked_response: HTTPXMock, use_async):

    filter = ""

    cli = OptimadeClient(base_urls=[TEST_URL], use_async=use_async)
    results = cli.get()
    assert results["structures"][filter][TEST_URL]["data"]
    assert results["structures"][filter][TEST_URL]["data"][0]["type"] == "structures"

    results = cli.structures.get()
    assert results["structures"][filter][TEST_URL]["data"]
    assert results["structures"][filter][TEST_URL]["data"][0]["type"] == "structures"

    results = cli.references.get()
    assert results["references"][filter][TEST_URL]["data"]
    assert results["references"][filter][TEST_URL]["data"][0]["type"] == "references"

    results = cli.get()
    assert results["structures"][filter][TEST_URL]["data"]
    assert results["structures"][filter][TEST_URL]["data"][0]["type"] == "structures"

    results = cli.references.count()
    assert results["references"][filter][TEST_URL] > 0

    filter = 'elements HAS "Ag"'
    results = cli.count(filter)
    assert results["structures"][filter][TEST_URL] > 0

    results = cli.info.get()
    assert results["info"][""][TEST_URL]["data"]["type"] == "info"

    results = cli.info.structures.get()
    assert "properties" in results["info/structures"][""][TEST_URL]["data"]


@pytest.mark.parametrize("use_async", [False])
def test_filter_validation(use_async):
    cli = OptimadeClient(use_async=use_async, base_urls=TEST_URL)
    with pytest.raises(Exception):
        cli.get("completely wrong filter")

    with pytest.raises(Exception):
        cli.get("elements HAS 'Ag'")


@pytest.mark.parametrize("use_async", [False])
def test_client_response_fields(httpx_mocked_response, use_async):
    cli = OptimadeClient(base_urls=[TEST_URL], use_async=use_async)
    results = cli.get(response_fields=["chemical_formula_reduced"])
    for d in results["structures"][""][TEST_URL]["data"]:
        assert "chemical_formula_reduced" in d["attributes"]
        assert len(d["attributes"]) == 1

    results = cli.get(
        response_fields=["chemical_formula_reduced", "cartesian_site_positions"]
    )
    for d in results["structures"][""][TEST_URL]["data"]:
        assert "chemical_formula_reduced" in d["attributes"]
        assert "cartesian_site_positions" in d["attributes"]
        assert len(d["attributes"]) == 2


@pytest.mark.parametrize("use_async", [False])
def test_multiple_base_urls(httpx_mocked_response, use_async):
    cli = OptimadeClient(base_urls=TEST_URLS, use_async=use_async)
    results = cli.get()
    count_results = cli.count()
    for url in TEST_URLS:
        assert len(results["structures"][""][url]["data"]) > 0
        assert (
            len(results["structures"][""][url]["data"])
            == count_results["structures"][""][url]
        )


@pytest.mark.parametrize("use_async", [False])
def test_client_sort(httpx_mocked_response, use_async):
    cli = OptimadeClient(base_urls=[TEST_URL], use_async=use_async)
    results = cli.get(sort="last_modified")
    assert len(results["structures"][""][TEST_URL]["data"]) > 0


def test_client_get_databases():
    try:
        cli = OptimadeClient()
        exited = False
    except SystemExit:
        exited = True
    assert exited or len(list(cli.base_urls)) > 15


@pytest.mark.parametrize("use_async", [False])
def test_command_line_client(httpx_mocked_response, use_async, capsys):
    args = dict(
        use_async=use_async,
        filter=['elements HAS "Ag"'],
        base_url=TEST_URLS,
        max_results_per_provider=100,
        output_file=None,
        count=False,
        response_fields=None,
        sort=None,
        endpoint="structures",
        pretty_print=False,
    )

    # Test multi-provider query
    _get(**args)
    captured = capsys.readouterr()
    assert 'Performing query structures/?filter=elements HAS "Ag"' in captured.err
    results = json.loads(captured.out)
    for url in TEST_URLS:
        assert len(results["structures"]['elements HAS "Ag"'][url]["data"]) == 11
        assert len(results["structures"]['elements HAS "Ag"'][url]["included"]) == 2
        assert len(results["structures"]['elements HAS "Ag"'][url]["links"]) == 2
        assert len(results["structures"]['elements HAS "Ag"'][url]["errors"]) == 0
        assert len(results["structures"]['elements HAS "Ag"'][url]["meta"]) > 0

    # Test multi-provider count
    args["count"] = True
    _get(**args)
    captured = capsys.readouterr()
    assert 'Counting results for structures/?filter=elements HAS "Ag"' in captured.err
    results = json.loads(captured.out)
    for url in TEST_URLS:
        assert results["structures"]['elements HAS "Ag"'][url] == 11
    args["count"] = False

    # Test writing to file
    test_filename = "test-optimade-client.json"
    if Path(test_filename).is_file():
        Path(test_filename).unlink()
    args["output_file"] = test_filename
    _get(**args)
    captured = capsys.readouterr()
    assert 'Performing query structures/?filter=elements HAS "Ag"' in captured.err
    assert not captured.out
    assert Path(test_filename).is_file()
    with open(test_filename, "r") as f:
        results = json.load(f)
    for url in TEST_URLS:
        assert len(results["structures"]['elements HAS "Ag"'][url]["data"]) == 11
        assert len(results["structures"]['elements HAS "Ag"'][url]["included"]) == 2
        assert len(results["structures"]['elements HAS "Ag"'][url]["links"]) == 2
        assert len(results["structures"]['elements HAS "Ag"'][url]["errors"]) == 0
        assert len(results["structures"]['elements HAS "Ag"'][url]["meta"]) > 0
    Path(test_filename).unlink()
