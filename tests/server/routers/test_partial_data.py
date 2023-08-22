from optimade.models import PartialDataResponse

from ..utils import RegularEndpointTests


class TestPartialDataEndpoint(RegularEndpointTests):
    """Tests for /partial_data/<entry_id>"""

    test_id = "mpf_551"
    params = "response_fields=cartesian_site_positions"
    request_str = f"/partial_data/{test_id}?{params}"
    response_cls = PartialDataResponse

    def test_structures_endpoint_data(self):
        pass
