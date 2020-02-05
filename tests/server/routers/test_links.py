# pylint: disable=relative-beyond-top-level
import unittest

from optimade.models import LinksResponse

from ..utils import EndpointTestsMixin, get_regular_client, get_index_client


class LinksEndpointTests(EndpointTestsMixin, unittest.TestCase):

    client = get_regular_client()
    request_str = "/links"
    response_cls = LinksResponse


class IndexLinksEndpointTests(EndpointTestsMixin, unittest.TestCase):

    client = get_index_client()
    request_str = "/links"
    response_cls = LinksResponse
