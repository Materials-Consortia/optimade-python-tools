from datetime import datetime, timezone

from optimade.server.routers import structures_coll


def fmt_datetime(object_: datetime) -> str:
    """Parse datetime into pydantic's JSON encoded datetime string"""
    return object_.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_int_asc(get_good_response):
    """Ascending sort (integer)"""
    limit = 5

    request = f"/structures?sort=nelements&page_limit={limit}"
    data = structures_coll.collection.find(sort=[("nelements", 1)], limit=limit)
    expected_nelements = [_["nelements"] for _ in data]

    response = get_good_response(request)
    nelements_list = [
        struct.get("attributes", {}).get("nelements") for struct in response["data"]
    ]
    assert nelements_list == expected_nelements


def test_int_desc(get_good_response):
    """Descending sort (integer)"""
    limit = 5

    request = f"/structures?sort=-nelements&page_limit={limit}"
    data = structures_coll.collection.find(sort=[("nelements", -1)], limit=limit)
    expected_nelements = [_["nelements"] for _ in data]

    response = get_good_response(request)
    nelements_list = [
        struct.get("attributes", {}).get("nelements") for struct in response["data"]
    ]
    assert nelements_list == expected_nelements


def test_str_asc(check_response):
    """Ascending sort (string)"""
    limit = 5

    request = f"/structures?sort=id&page_limit={limit}"
    data = structures_coll.collection.find(sort=[("task_id", 1)])
    expected_ids = [_["task_id"] for _ in data]
    check_response(
        request, expected_ids=expected_ids, page_limit=limit,
    )


def test_str_desc(check_response):
    """Descending sort (string)"""
    limit = 5

    request = f"/structures?sort=-id&page_limit={limit}"
    data = structures_coll.collection.find(sort=[("task_id", -1)])
    expected_ids = [_["task_id"] for _ in data]
    check_response(
        request, expected_ids=expected_ids, expected_as_is=True, page_limit=limit,
    )


def test_datetime_asc(get_good_response):
    """Ascending sort (datetime)"""
    limit = 5

    request = f"/structures?sort=last_modified&page_limit={limit}"
    data = structures_coll.collection.find(sort=[("last_modified", 1)], limit=limit)
    expected_last_modified = [fmt_datetime(_["last_modified"]) for _ in data]

    response = get_good_response(request)
    last_modified_list = [
        struct.get("attributes", {}).get("last_modified") for struct in response["data"]
    ]
    assert last_modified_list == expected_last_modified


def test_datetime_desc(get_good_response):
    """Descending sort (datetime)"""
    limit = 5

    request = f"/structures?sort=-last_modified&page_limit={limit}"
    data = structures_coll.collection.find(sort=[("last_modified", -1)], limit=limit)
    expected_last_modified = [fmt_datetime(_["last_modified"]) for _ in data]

    response = get_good_response(request)
    last_modified_list = [
        struct.get("attributes", {}).get("last_modified") for struct in response["data"]
    ]
    assert last_modified_list == expected_last_modified
