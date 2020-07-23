from datetime import datetime, timezone

import pytest


@pytest.fixture(scope="module")
def structures():
    """Get structures_coll collection"""
    from optimade.server.routers import structures_coll

    return structures_coll


def fmt_datetime(object_: datetime) -> str:
    """Parse datetime into pydantic's JSON encoded datetime string"""
    return object_.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_int_asc(get_good_response, structures):
    """Ascending sort (integer)"""
    limit = 5

    request = f"/structures?sort=nelements&page_limit={limit}"
    data = structures.collection.find(sort=[("nelements", 1)], limit=limit)
    expected_nelements = [_["nelements"] for _ in data]

    response = get_good_response(request)
    nelements_list = [
        struct.get("attributes", {}).get("nelements") for struct in response["data"]
    ]
    assert nelements_list == expected_nelements


def test_int_desc(get_good_response, structures):
    """Descending sort (integer)"""
    limit = 5

    request = f"/structures?sort=-nelements&page_limit={limit}"
    data = structures.collection.find(sort=[("nelements", -1)], limit=limit)
    expected_nelements = [_["nelements"] for _ in data]

    response = get_good_response(request)
    nelements_list = [
        struct.get("attributes", {}).get("nelements") for struct in response["data"]
    ]
    assert nelements_list == expected_nelements


def test_str_asc(check_response, structures):
    """Ascending sort (string)"""
    limit = 5

    request = f"/structures?sort=id&page_limit={limit}"
    data = structures.collection.find(sort=[("task_id", 1)])
    expected_ids = [_["task_id"] for _ in data]
    check_response(
        request, expected_ids=expected_ids, page_limit=limit,
    )


def test_str_desc(check_response, structures):
    """Descending sort (string)"""
    limit = 5

    request = f"/structures?sort=-id&page_limit={limit}"
    data = structures.collection.find(sort=[("task_id", -1)])
    expected_ids = [_["task_id"] for _ in data]
    check_response(
        request, expected_ids=expected_ids, expected_as_is=True, page_limit=limit,
    )


def test_datetime_asc(get_good_response, structures):
    """Ascending sort (datetime)"""
    limit = 5

    request = f"/structures?sort=last_modified&page_limit={limit}"
    data = structures.collection.find(sort=[("last_modified", 1)], limit=limit)
    expected_last_modified = [fmt_datetime(_["last_modified"]) for _ in data]

    response = get_good_response(request)
    last_modified_list = [
        struct.get("attributes", {}).get("last_modified") for struct in response["data"]
    ]
    assert last_modified_list == expected_last_modified


def test_datetime_desc(get_good_response, structures):
    """Descending sort (datetime)"""
    limit = 5

    request = f"/structures?sort=-last_modified&page_limit={limit}"
    data = structures.collection.find(sort=[("last_modified", -1)], limit=limit)
    expected_last_modified = [fmt_datetime(_["last_modified"]) for _ in data]

    response = get_good_response(request)
    last_modified_list = [
        struct.get("attributes", {}).get("last_modified") for struct in response["data"]
    ]
    assert last_modified_list == expected_last_modified


def test_unknown_fields(get_good_response, check_error_response, structures):
    """Sorting with one valid field and many other *implementation-specific* fields should return only
    sorted data on the valid field.

    If *only* implementation-specific fields are provided, then raise a `BadRequest`.

    If *any* invalid field, i.e. one without an implementation specific prefix is supplied,
    a `BadRequest` should be raised.

    """

    # case 1: non-prefixed field that does not exist
    limit = 5
    request = f"/structures?sort=field_that_does_not_exist&page_limit={limit}"
    check_error_response(
        request,
        expected_status=400,
        expected_title="Bad Request",
        expected_detail="Unable to sort on unknown field 'field_that_does_not_exist'",
    )

    # case 2: multiple non-prefixed fields that do not exist
    request = f"/structures?sort=field_that_does_not_exist,-other_field_that_does_not_exist&page_limit={limit}"
    check_error_response(
        request,
        expected_status=400,
        expected_title="Bad Request",
        expected_detail="Unable to sort on unknown fields 'field_that_does_not_exist', 'other_field_that_does_not_exist'",
    )

    # case 3: prefixed field and a valid field should be fine
    request = f"/structures?sort=_exmpl_field_that_does_not_exist,nelements&page_limit={limit}"
    data = structures.collection.find(sort=[("nelements", 1)], limit=limit)
    expected_nelements = [_["nelements"] for _ in data]

    response = get_good_response(request)
    nelements_list = [
        struct.get("attributes", {}).get("nelements") for struct in response["data"]
    ]
    assert nelements_list == expected_nelements

    # case 4: unprefixed field and a valid field should fail
    request = f"/structures?sort=field_that_does_not_exist,nelements&page_limit={limit}"
    check_error_response(
        request,
        expected_status=400,
        expected_title="Bad Request",
        expected_detail="Unable to sort on unknown field 'field_that_does_not_exist'",
    )

    # case 5: only prefixed fields
    request = f"/structures?sort=_exmpl_field_that_does_not_exist,_exmpl_other_field&page_limit={limit}"
    check_error_response(
        request,
        expected_status=400,
        expected_title="Bad Request",
        expected_detail="Unable to sort on unknown fields '_exmpl_field_that_does_not_exist', '_exmpl_other_field'",
    )
