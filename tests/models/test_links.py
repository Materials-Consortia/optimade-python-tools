# pylint: disable=no-member
import pytest

from optimade.models.links import LinksResource
from optimade.server.mappers import LinksMapper


def test_good_links(starting_links):
    """Check well-formed links used as example data"""
    import optimade.server.data

    good_refs = optimade.server.data.links
    for doc in good_refs:
        LinksResource(**LinksMapper.map_back(doc))

    # Test starting_links is a good links resource
    LinksResource(**LinksMapper.map_back(starting_links))


def test_bad_links(starting_links):
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
        print(f"Now testing number {index}")
        bad_link = starting_links.copy()
        bad_link.update(links)
        with pytest.raises(ValidationError):
            LinksResource(**LinksMapper.map_back(bad_link))
        del bad_link
