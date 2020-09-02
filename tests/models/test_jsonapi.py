from pydantic import ValidationError
import pytest
from optimade.models.jsonapi import Error, ToplevelLinks


def test_hashability():
    error = Error(id="test")
    assert set([error])


def test_toplevel_links():
    """Test top-level links responses as both URLs and Links objects,
    and check that any arbitrary key is allowed as long as the value
    can be validated as a URL or a Links object too.

    """
    test_links = {
        "first": {"href": "http://example.org/structures?page_limit=3&page_offset=0"},
        "last": {"href": "http://example.org/structures?page_limit=3&page_offset=10"},
        "prev": {
            "href": "http://example.org/structures?page_limit=3&page_offset=2",
            "meta": {"description": "the previous link"},
        },
        "next": {
            "href": "http://example.org/structures?page_limit=3&page_offset=3",
            "meta": {"description": "the next link"},
        },
    }

    # Test all defined fields as URLs and Links objects
    for link in test_links:
        assert ToplevelLinks(**{link: test_links[link]})
        assert ToplevelLinks(**{link: test_links[link]["href"]})

    # Allow arbitrary keys are as long as they are links
    assert ToplevelLinks(
        **{
            "base_url": "https://example.org/structures",
            "other_url": {"href": "https://example.org"},
        }
    )
    assert ToplevelLinks(
        **{
            "base_url5": {
                "href": "https://example.org/structures",
                "meta": {"description": "the base URL"},
            },
            "none_url": None,
        }
    )

    # Check that non-URL and non-Links objects will fail to validate
    with pytest.raises(ValidationError):
        ToplevelLinks(**{"base_url": {"this object": "is not a URL or a Links object"}})

    with pytest.raises(ValidationError):
        ToplevelLinks(**{"base_url": {"href": "not a link"}})
