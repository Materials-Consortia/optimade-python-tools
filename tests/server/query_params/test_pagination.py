"""Make sure filters are handled correctly"""

from optimade.server.config import CONFIG, SupportedBackend


def test_default_pagination(check_response):
    request = "/structures?page_limit=1"
    expected_ids = ["mpf_1"]
    response = check_response(request, expected_ids)
    if CONFIG.database_backend in (
        SupportedBackend.MONGODB,
        SupportedBackend.MONGOMOCK,
    ):
        assert "page_offset" in response.links.next
    if CONFIG.database_backend == SupportedBackend.ELASTIC:
        assert "page_above" in response.links.next
