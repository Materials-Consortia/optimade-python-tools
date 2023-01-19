from optimade import __api_version__

from ..utils import NoJsonEndpointTests


class TestVersionsEndpoint(NoJsonEndpointTests):

    request_str = "/versions"
    response_cls = str

    def test_versions_endpoint(self):
        assert (
            self.response.text
            == f"version\n{__api_version__.replace('v', '').split('.')[0]}"
        )
        assert "text/csv" in self.response.headers.get("content-type")
        assert "header=present" in self.response.headers.get("content-type")
