# pylint: disable=no-member
import pytest

from optimade.models.links import LinksResource

MAPPER = "LinksMapper"


def test_good_links(starting_links, mapper):
    """Check well-formed links used as example data"""
    # Test starting_links is a good links resource
    LinksResource(**mapper(MAPPER).map_back(starting_links))


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
