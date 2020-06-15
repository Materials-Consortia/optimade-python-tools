import pytest


def load_test_data(filename: str) -> list:
    """Utility function to load JSON files from 'test_data'"""
    import json
    from pathlib import Path

    json_file_path = (
        Path(__file__).parent.joinpath("test_data").joinpath(filename).resolve()
    )
    if not json_file_path.exists():
        raise RuntimeError(f"Could not find {filename!r} in 'tests.models.test_data'")

    with open(json_file_path, "r") as handle:
        data = json.load(handle)

    return data


def remove_mongo_date(resources: list) -> list:
    """Utility function to remove and flatten nested $date properties"""
    res = []
    for document in resources:
        updated_document = document.copy()
        for field, value in document.items():
            if isinstance(value, dict) and "$date" in value:
                updated_document.update({field: value["$date"]})
        res.append(updated_document)
        del updated_document
    return res


@pytest.fixture(scope="session")
def bad_structures() -> list:
    """Load and return list of bad structures resources"""
    filename = "test_bad_structures.json"
    structures = load_test_data(filename)
    structures = remove_mongo_date(structures)
    return structures


@pytest.fixture(scope="session")
def good_structures() -> list:
    """Load and return list of good structures resources"""
    filename = "test_good_structures.json"
    structures = load_test_data(filename)
    structures = remove_mongo_date(structures)
    return structures
