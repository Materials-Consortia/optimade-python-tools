import pytest

from optimade.models import LinksResponse
from optimade.models.links import Aggregate, LinksResource, LinkType

MAPPER = "LinksMapper"


def test_good_links(starting_links, mapper):
    """Check well-formed links used as example data"""
    # Test starting_links is a good links resource
    resource = LinksResource(**mapper(MAPPER).map_back(starting_links))
    assert resource.attributes.link_type == LinkType.CHILD
    assert resource.attributes.aggregate == Aggregate.TEST


def test_edge_case_links():
    response = LinksResponse(
        data=[
            {
                "id": "aflow",
                "type": "links",
                "attributes": {
                    "name": "AFLOW",
                    "description": "The AFLOW OPTIMADE endpoint",
                    "base_url": "http://aflow.org/API/optimade/",
                    "homepage": "http://aflow.org",
                    "link_type": "child",
                },
            },
        ],
        meta={
            "query": {"representation": "/links"},
            "more_data_available": False,
            "api_version": "1.0.0",
        },
    )

    assert isinstance(response.data[0], LinksResource)
    assert response.data[0].attributes.link_type == LinkType.CHILD


def test_bad_links(starting_links, mapper):
    """Check badly formed links"""
    from pydantic import ValidationError

    bad_links = [
        {"aggregate": "wrong"},
        {"link_type": "wrong"},
        {"base_url": "example.org"},
        {"homepage": "www.example.org"},
        {"relationships": {}},
    ]

    for index, links in enumerate(bad_links):
        # This is for helping devs finding any errors that may occur
        print(f"Now testing number {index}")
        bad_link = starting_links.copy()
        bad_link.update(links)
        with pytest.raises(ValidationError):
            LinksResource(**mapper(MAPPER).map_back(bad_link))
        del bad_link
