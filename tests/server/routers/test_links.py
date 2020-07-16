from optimade.models import LinksResponse

from ..utils import EndpointTests


class TestLinksEndpoint(EndpointTests):

    request_str = "/links"
    response_cls = LinksResponse
