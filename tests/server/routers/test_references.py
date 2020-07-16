from optimade.models import ReferenceResponseMany, ReferenceResponseOne

from ..utils import RegularEndpointTests


class TestReferencesEndpoint(RegularEndpointTests):

    request_str = "/references"
    response_cls = ReferenceResponseMany


class TestSingleReferenceEndpoint(RegularEndpointTests):

    test_id = "dijkstra1968"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne


class TestSingleReferenceEndpointDifficult(RegularEndpointTests):

    test_id = "dummy/20.19"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne


class TestMissingSingleReferenceEndpoint(RegularEndpointTests):
    """Tests for /references/<entry_id> for unknown <entry_id>"""

    test_id = "random_string_that_is_not_in_test_data"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne

    def test_references_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert "meta" in self.json_response
        assert self.json_response["data"] is None
        assert self.json_response["meta"]["data_returned"] == 0
        assert not self.json_response["meta"]["more_data_available"]
