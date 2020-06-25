import pytest

from optimade.models.baseinfo import AvailableApiVersion


def test_available_api_versions():
    """Check version formatting for available_api_versions"""

    bad_urls = [
        {"url": "asfdsafhttps://example.com/v0.0", "version": "0.0.0"},
        {"url": "https://example.com/optimade", "version": "1.0.0"},
        {"url": "https://example.com/v0999", "version": "0999.0.0"},
        {"url": "http://example.com/v2.3", "version": "2.3.0"},
        {"url": "https://example.com/v1.0.0-rc.2", "version": "1.0.0-rc.2"},
    ]
    good_urls = [
        {"url": "https://example.com/v0", "version": "0.1.9"},
        {"url": "https://example.com/v1.0.2", "version": "1.0.2"},
        {"url": "https://example.com/optimade/v1.2", "version": "1.2.3"},
        {"url": "https://example.com/v1.0.0", "version": "1.0.0-rc.2"},
    ]
    bad_combos = [
        {"url": "https://example.com/v0", "version": "1.0.0"},
        {"url": "https://example.com/v1.0.2", "version": "1.0.3"},
        {"url": "https://example.com/optimade/v1.2", "version": "1.3.2"},
    ]

    for data in bad_urls:
        with pytest.raises(ValueError) as exc:
            AvailableApiVersion(**data)
        assert (
            "url MUST be a versioned base URL" in exc.exconly()
            or "URL scheme not permitted" in exc.exconly()
        ), f"Validator 'url_must_be_versioned_base_url' not triggered as it should.\nException message: {exc.exconly()}.\nInputs: {data}"

    for data in bad_combos:
        with pytest.raises(ValueError) as exc:
            AvailableApiVersion(**data)
        assert "is not compatible with url version" in exc.exconly(), (
            f"Validator 'crosscheck_url_and_version' not triggered as it should.\nException message: {exc.exconly()}.\nInputs: {data}",
        )

    for data in good_urls:
        assert isinstance(AvailableApiVersion(**data), AvailableApiVersion)
