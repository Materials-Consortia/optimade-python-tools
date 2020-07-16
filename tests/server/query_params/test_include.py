"""Make sure `include` is handled correctly

NOTE: Currently _only_ structures have relationships (references).
"""


def test_default_value(check_include_response):
    """Default value for `include` is 'references'

    Test also that passing `include=` equals passing the default value
    """
    request = "/structures"
    expected_types = ["references"]
    expected_reference_ids = ["dijkstra1968", "maddox1988", "dummy/2019"]
    check_include_response(
        request,
        expected_included_types=expected_types,
        expected_included_resources=expected_reference_ids,
    )


def test_empty_value(check_include_response):
    """An empty value should resolve in no relationships being returned under `included`"""
    request = "/structures?include="
    expected_types = []
    expected_reference_ids = []
    expected_data_relationship_types = ["references"]
    check_include_response(
        request,
        expected_included_types=expected_types,
        expected_included_resources=expected_reference_ids,
        expected_relationship_types=expected_data_relationship_types,
    )


def test_default_value_single_entry(check_include_response):
    """For single entry. Default value for `include` is 'references'"""
    request = "/structures/mpf_1"
    expected_types = ["references"]
    expected_reference_ids = ["dijkstra1968"]
    check_include_response(
        request,
        expected_included_types=expected_types,
        expected_included_resources=expected_reference_ids,
    )


def test_empty_value_single_entry(check_include_response):
    """For single entry. An empty value should resolve in no relationships being returned under `included`"""
    request = "/structures/mpf_1?include="
    expected_types = []
    expected_reference_ids = []
    expected_data_relationship_types = ["references"]
    check_include_response(
        request,
        expected_included_types=expected_types,
        expected_included_resources=expected_reference_ids,
        expected_relationship_types=expected_data_relationship_types,
    )


def test_wrong_relationship_type(check_error_response):
    """A wrong type should result in a `400 Bad Request` response"""
    from optimade.server.routers import ENTRY_COLLECTIONS

    for wrong_type in ("test", '""', "''"):
        request = f"/structures?include={wrong_type}"
        error_detail = (
            f"'{wrong_type}' cannot be identified as a valid relationship type. "
            f"Known relationship types: {sorted(ENTRY_COLLECTIONS.keys())}"
        )
        check_error_response(
            request,
            expected_status=400,
            expected_title="Bad Request",
            expected_detail=error_detail,
        )
