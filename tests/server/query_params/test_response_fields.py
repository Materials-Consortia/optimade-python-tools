"""Make sure response_fields is handled correctly"""


def test_required_fields_links(check_required_fields_response):
    """Certain fields are REQUIRED, no matter the value of `response_fields`"""
    endpoint = "links"
    illegal_top_level_field = "relationships"
    non_used_top_level_fields = {"links"}
    non_used_top_level_fields.add(illegal_top_level_field)
    expected_fields = {"homepage", "base_url", "link_type"}
    check_required_fields_response(endpoint, non_used_top_level_fields, expected_fields)


def test_required_fields_references(check_required_fields_response):
    """Certain fields are REQUIRED, no matter the value of `response_fields`"""
    endpoint = "references"
    non_used_top_level_fields = {"links", "relationships"}
    expected_fields = {"year", "journal"}
    check_required_fields_response(endpoint, non_used_top_level_fields, expected_fields)


def test_required_fields_structures(check_required_fields_response):
    """Certain fields are REQUIRED, no matter the value of `response_fields`"""
    endpoint = "structures"
    non_used_top_level_fields = {"links"}
    expected_fields = {"elements", "nelements"}
    check_required_fields_response(endpoint, non_used_top_level_fields, expected_fields)
