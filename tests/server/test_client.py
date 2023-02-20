"""This module uses the reference test server to test the OPTIMADE client."""


import json
from functools import partial
from pathlib import Path
from typing import Dict, Optional

import httpx
import pytest

from optimade.client.cli import _get
from optimade.warnings import MissingExpectedField

try:
    from optimade.client import OptimadeClient as OptimadeTestClient
except ImportError as exc:
    pytest.skip(str(exc), allow_module_level=True)


class OptimadeClient(OptimadeTestClient):
    """Wrapper to the base OptimadeClient that enables strict mode for testing."""

    __strict_async = True


TEST_URLS = [
    "https://example.com",
    "https://example.org",
    "https://optimade.fly.dev",
]
TEST_URL = TEST_URLS[0]


@pytest.mark.parametrize(
    "use_async",
    [True, False],
)
def test_client_endpoints(async_http_client, http_client, use_async):
    filter = ""

    cli = OptimadeClient(
        base_urls=[TEST_URL],
        use_async=use_async,
        http_client=async_http_client if use_async else http_client,
    )
    get_results = cli.get()
    assert get_results["structures"][filter][TEST_URL]["data"]
    assert (
        get_results["structures"][filter][TEST_URL]["data"][0]["type"] == "structures"
    )

    get_results = cli.structures.get()
    assert get_results["structures"][filter][TEST_URL]["data"]
    assert (
        get_results["structures"][filter][TEST_URL]["data"][0]["type"] == "structures"
    )

    get_results = cli.references.get()
    assert get_results["references"][filter][TEST_URL]["data"]
    assert (
        get_results["references"][filter][TEST_URL]["data"][0]["type"] == "references"
    )

    get_results = cli.get()
    assert get_results["structures"][filter][TEST_URL]["data"]
    assert (
        get_results["structures"][filter][TEST_URL]["data"][0]["type"] == "structures"
    )

    count_results = cli.references.count()
    assert count_results["references"][filter][TEST_URL] > 0

    filter = 'elements HAS "Ag"'
    count_results = cli.count(filter)
    assert count_results["structures"][filter][TEST_URL] > 0

    count_results = cli.info.get()
    assert count_results["info"][""][TEST_URL]["data"]["type"] == "info"

    count_results = cli.info.structures.get()
    assert "properties" in count_results["info/structures"][""][TEST_URL]["data"]


@pytest.mark.parametrize("use_async", [True, False])
def test_filter_validation(async_http_client, http_client, use_async):
    cli = OptimadeClient(
        use_async=use_async,
        base_urls=TEST_URL,
        http_client=async_http_client if use_async else http_client,
    )
    with pytest.raises(Exception):
        cli.get("completely wrong filter")

    with pytest.raises(Exception):
        cli.get("elements HAS 'Ag'")


@pytest.mark.parametrize("use_async", [True, False])
def test_client_response_fields(async_http_client, http_client, use_async):
    with pytest.warns(MissingExpectedField):
        cli = OptimadeClient(
            base_urls=[TEST_URL],
            use_async=use_async,
            http_client=async_http_client if use_async else http_client,
        )
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


@pytest.mark.parametrize("use_async", [True, False])
def test_multiple_base_urls(async_http_client, http_client, use_async):
    cli = OptimadeClient(
        base_urls=TEST_URLS,
        use_async=use_async,
        http_client=async_http_client if use_async else http_client,
    )
    results = cli.get()
    count_results = cli.count()
    for url in TEST_URLS:
        assert len(results["structures"][""][url]["data"]) > 0
        assert (
            len(results["structures"][""][url]["data"])
            == count_results["structures"][""][url]
        )


@pytest.mark.parametrize("use_async", [True, False])
def test_include_exclude_providers(async_http_client, http_client, use_async):
    with pytest.raises(
        SystemExit,
        match="Unable to access any OPTIMADE base URLs. If you believe this is an error, try manually specifying some base URLs.",
    ):
        OptimadeClient(
            include_providers={"exmpl"},
            exclude_providers={"exmpl"},
            use_async=use_async,
            http_client=async_http_client if use_async else http_client,
        )

    with pytest.raises(
        RuntimeError,
        match="Cannot provide both a list of base URLs and included/excluded databases.",
    ):
        OptimadeClient(
            base_urls=TEST_URLS,
            include_providers={"exmpl"},
            use_async=use_async,
            http_client=async_http_client if use_async else http_client,
        )

    with pytest.raises(
        SystemExit,
        match="Unable to access any OPTIMADE base URLs. If you believe this is an error, try manually specifying some base URLs.",
    ):
        OptimadeClient(
            include_providers={"exmpl"},
            exclude_databases={"https://example.org/optimade"},
            use_async=use_async,
            http_client=async_http_client if use_async else http_client,
        )


@pytest.mark.parametrize("use_async", [True, False])
def test_client_sort(async_http_client, http_client, use_async):
    cli = OptimadeClient(
        base_urls=[TEST_URL],
        use_async=use_async,
        http_client=async_http_client if use_async else http_client,
    )
    results = cli.get(sort="last_modified")
    assert len(results["structures"][""][TEST_URL]["data"]) > 0


@pytest.mark.parametrize("use_async", [True, False])
def test_command_line_client(async_http_client, http_client, use_async, capsys):
    args = dict(
        use_async=use_async,
        filter=['elements HAS "Ag"'],
        base_url=TEST_URLS,
        max_results_per_provider=100,
        output_file=None,
        count=False,
        response_fields=None,
        sort=None,
        silent=False,
        endpoint="structures",
        pretty_print=False,
        include_providers=None,
        exclude_providers=None,
        exclude_databases=None,
        http_client=async_http_client if use_async else http_client,
        http_timeout=httpx.Timeout(2.0),
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


@pytest.mark.parametrize("use_async", [True, False])
def test_command_line_client_silent(async_http_client, http_client, use_async, capsys):
    args = dict(
        use_async=use_async,
        filter=['elements HAS "Ag"'],
        base_url=TEST_URLS,
        max_results_per_provider=100,
        output_file=None,
        count=False,
        response_fields=None,
        sort=None,
        silent=True,
        endpoint="structures",
        pretty_print=False,
        include_providers=None,
        exclude_providers=None,
        exclude_databases=None,
        http_client=async_http_client if use_async else http_client,
        http_timeout=httpx.Timeout(2.0),
    )

    # Test silent mode
    _get(**args)
    captured = capsys.readouterr()
    assert 'Performing query structures/?filter=elements HAS "Ag"' not in captured.err
    results = json.loads(captured.out)
    for url in TEST_URLS:
        assert len(results["structures"]['elements HAS "Ag"'][url]["data"]) == 11
        assert len(results["structures"]['elements HAS "Ag"'][url]["included"]) == 2
        assert len(results["structures"]['elements HAS "Ag"'][url]["links"]) == 2
        assert len(results["structures"]['elements HAS "Ag"'][url]["errors"]) == 0
        assert len(results["structures"]['elements HAS "Ag"'][url]["meta"]) > 0


@pytest.mark.parametrize("use_async", [True, False])
def test_command_line_client_multi_provider(
    async_http_client, http_client, use_async, capsys
):
    # Test multi-provider count
    args = dict(
        count=True,
        use_async=use_async,
        filter=['elements HAS "Ag"'],
        base_url=TEST_URLS,
        max_results_per_provider=100,
        output_file=None,
        response_fields=None,
        sort=None,
        silent=False,
        endpoint="structures",
        pretty_print=False,
        include_providers=None,
        exclude_providers=None,
        exclude_databases=None,
        http_client=async_http_client if use_async else http_client,
        http_timeout=httpx.Timeout(2.0),
    )
    _get(**args)
    captured = capsys.readouterr()
    assert 'Counting results for structures/?filter=elements HAS "Ag"' in captured.err
    results = json.loads(captured.out)
    for url in TEST_URLS:
        assert results["structures"]['elements HAS "Ag"'][url] == 11
    args["count"] = False


@pytest.mark.parametrize("use_async", [True, False])
def test_command_line_client_write_to_file(
    async_http_client, http_client, use_async, capsys
):
    # Test writing to file
    args = dict(
        use_async=use_async,
        filter=['elements HAS "Ag"'],
        base_url=TEST_URLS,
        max_results_per_provider=100,
        output_file=None,
        count=False,
        response_fields=None,
        sort=None,
        silent=False,
        endpoint="structures",
        pretty_print=False,
        include_providers=None,
        exclude_providers=None,
        exclude_databases=None,
        http_client=async_http_client if use_async else http_client,
        http_timeout=httpx.Timeout(2.0),
    )
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


@pytest.mark.parametrize("use_async", [True, False])
def test_strict_async(async_http_client, http_client, use_async):
    with pytest.raises(RuntimeError):
        _ = OptimadeClient(
            base_urls=TEST_URLS,
            use_async=use_async,
            http_client=http_client if use_async else async_http_client,
        )


@pytest.mark.parametrize("use_async", [True, False])
def test_client_global_data_callback(async_http_client, http_client, use_async):
    container: Dict[str, str] = {}

    def global_database_callback(_: str, results: Dict):
        """A test callback that creates a flat dictionary of results via global state"""

        for structure in results["data"]:
            container[structure["id"]] = structure["attributes"][
                "chemical_formula_reduced"
            ]

        return None

    cli = OptimadeClient(
        base_urls=[TEST_URL],
        use_async=use_async,
        http_client=async_http_client if use_async else http_client,
        callbacks=[global_database_callback],
    )

    cli.get(response_fields=["chemical_formula_reduced"])

    assert len(container) == 17


@pytest.mark.parametrize("use_async", [True, False])
def test_client_mutable_data_callback(async_http_client, http_client, use_async):
    container: Dict[str, str] = {}

    def mutable_database_callback(
        _: str, results: Dict, db: Optional[Dict[str, str]] = None
    ) -> None:
        """A test callback that creates a flat dictionary of results via mutable args."""

        if db is None:
            return

        for structure in results["data"]:
            db[structure["id"]] = structure["attributes"]["chemical_formula_reduced"]

    cli = OptimadeClient(
        base_urls=[TEST_URL],
        use_async=use_async,
        http_client=async_http_client if use_async else http_client,
        callbacks=[partial(mutable_database_callback, db=container)],
    )

    cli.get(response_fields=["chemical_formula_reduced"])

    assert len(container) == 17


@pytest.mark.parametrize("use_async", [True, False])
def test_client_asynchronous_write_callback(
    async_http_client, http_client, use_async, tmp_path
):
    def write_to_file(_: str, results: Dict):
        """A test callback that creates a flat dictionary of results via global state"""

        with open(tmp_path / "formulae.csv", "a") as f:
            for structure in results["data"]:
                f.write(
                    f'\n{structure["id"]}, {structure["attributes"]["chemical_formula_reduced"]}'
                )

        return None

    cli = OptimadeClient(
        base_urls=TEST_URLS,
        use_async=use_async,
        http_client=async_http_client if use_async else http_client,
        callbacks=[write_to_file],
    )

    cli.__strict_async = True

    cli.get(response_fields=["chemical_formula_reduced"])

    with open(tmp_path / "formulae.csv", "r") as f:
        lines = f.readlines()

    assert len(lines) == 17 * len(TEST_URLS) + 1
