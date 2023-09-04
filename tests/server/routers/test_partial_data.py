from optimade.models import PartialDataResponse

from ..utils import NoJsonEndpointTests


class TestPartialDataEndpoint(NoJsonEndpointTests):
    """Tests for /partial_data/<entry_id>"""

    test_id = "mpf_551"
    params = "response_fields=cartesian_site_positions"
    request_str = f"/partial_data/{test_id}?{params}"
    response_cls = PartialDataResponse


def test_wrong_id_partial_data(check_error_response, client):
    """If a non-supported versioned base URL is passed, `553 Version Not Supported` should be returned

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
