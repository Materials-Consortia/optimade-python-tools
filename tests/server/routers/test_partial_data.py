import pytest

from optimade.models import PartialDataResponse
from optimade.server.config import CONFIG

from ..utils import NoJsonEndpointTests


@pytest.mark.skipif(
    CONFIG.database_backend.value not in ("mongomock", "mongodb"),
    reason="At the moment partial data is only supported for the MongoDB backend",
)
class TestPartialDataEndpoint(NoJsonEndpointTests):
    """Tests for /partial_data/<entry_id>"""

    test_id = "mpf_551"
    params = "response_fields=cartesian_site_positions"
    request_str = f"/partial_data/{test_id}?{params}"
    response_cls = PartialDataResponse


@pytest.mark.skipif(
    CONFIG.database_backend.value not in ("mongomock", "mongodb"),
    reason="At the moment partial data is only supported for the MongoDB backend",
)
def test_property_ranges_link(get_good_response, client):
    test_id = "mpf_551"
    params = "response_fields=cartesian_site_positions&property_ranges=dim_sites:2:74:1,dim_cartesian_dimensions:1:3:1&response_format=json"
    request = f"/partial_data/{test_id}?{params}"
    get_good_response(
        request, server=client
    )  # todo expand test to check content better.


@pytest.mark.skipif(
    CONFIG.database_backend.value not in ("mongomock", "mongodb"),
    reason="At the moment partial data is only supported for the MongoDB backend",
)
def test_wrong_id_partial_data(check_error_response, client):
    """
    A specific JSON response should also occur.
    """
    test_id = "mpf_486"
    params = "response_fields=cartesian_site_positions"
    request = f"/partial_data/{test_id}?{params}"
    check_error_response(
        request,
        expected_status=404,
        expected_title="Not Found",
        expected_detail="No data available for the combination of entry mpf_486 and property cartesian_site_positions",
        server=client,
    )
