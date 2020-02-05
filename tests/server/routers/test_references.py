# pylint: disable=relative-beyond-top-level
import unittest

from optimade.models import ReferenceResponseMany, ReferenceResponseOne

from ..utils import EndpointTestsMixin, get_regular_client


class ReferencesEndpointTests(EndpointTestsMixin, unittest.TestCase):

    client = get_regular_client()
    request_str = "/references"
    response_cls = ReferenceResponseMany


class SingleReferenceEndpointTests(EndpointTestsMixin, unittest.TestCase):

    client = get_regular_client()
    test_id = "dijkstra1968"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne
