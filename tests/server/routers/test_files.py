from optimade.models import FileResponseMany, FileResponseOne

from ..utils import RegularEndpointTests


class TestFilesEndpoint(RegularEndpointTests):
    """Tests for /files"""

    request_str = "/files"
    response_cls = FileResponseMany

    def test_files_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "meta" in self.json_response
        assert self.json_response["meta"]["data_available"] == 3
        assert not self.json_response["meta"]["more_data_available"]
        assert "data" in self.json_response
        assert (
            len(self.json_response["data"])
            == self.json_response["meta"]["data_available"]
        )


class TestSingleFileEndpoint(RegularEndpointTests):
    """Tests for /files/<entry_id>"""

    test_id = "file_1"
    request_str = f"/files/{test_id}"
    response_cls = FileResponseOne

    def test_single_file_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert self.json_response["data"]["id"] == self.test_id
        assert self.json_response["data"]["type"] == "files"
        assert "attributes" in self.json_response["data"]
        assert "url" in self.json_response["data"]["attributes"]
        assert "name" in self.json_response["data"]["attributes"]


def test_check_response_single_file(check_response):
    """Tests whether check_response also handles single endpoint queries correctly."""
    request = "/files/file_1?response_fields=url"
    check_response(request, expected_ids="file_1")


class TestMissingSingleFileEndpoint(RegularEndpointTests):
    """Tests for /files/<entry_id> for unknown <entry_id>"""

    test_id = "random_string_that_is_not_in_test_data"
    request_str = f"/files/{test_id}"
    response_cls = FileResponseOne

    def test_missing_file_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert "meta" in self.json_response
        assert self.json_response["data"] is None
        assert self.json_response["meta"]["data_returned"] == 0
        assert not self.json_response["meta"]["more_data_available"]
