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


@pytest.fixture(scope="session")
def good_references() -> list:
    """Load and return list of good structures resources"""
    filename = "test_good_references.json"
    references = load_test_data(filename)
    references = remove_mongo_date(references)
    return references


@pytest.fixture
def starting_links() -> dict:
    """A good starting links resource"""
    return {
        "id": "test",
        "type": "links",
        "name": "Test",
        "description": "This is a test",
        "base_url": "https://example.org/optimade",
        "homepage": "https://example.org",
        "link_type": "child",
        "aggregate": "test",
        "no_aggregate_reason": "This is a test database",
    }


@pytest.fixture(scope="function")
def good_structure() -> dict:
    """Returns a 'good' structure that does not need to be mapped, which can be
    deformed to test different validators.

    """
    import datetime

    return {
        "id": "db/1234567",
        "type": "structures",
        "attributes": {
            "last_modified": datetime.datetime.now(),
            "elements": ["Ge", "Si"],
            "nsites": 3,
            "nelements": 2,
            "elements_ratios": [0.5, 0.5],
            "chemical_formula_reduced": "GeSi",
            "chemical_formula_hill": "GeSi",
            "chemical_formula_descriptive": "GeSi",
            "chemical_formula_anonymous": "AB",
            "dimension_types": [1, 1, 1],
            "nperiodic_dimensions": 3,
            "lattice_vectors": [[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 1.0, 4.0]],
            "cartesian_site_positions": [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            "species": [
                {"name": "Si", "chemical_symbols": ["Si"], "concentration": [1.0]},
                {"name": "Ge", "chemical_symbols": ["Ge"], "concentration": [1.0]},
                {
                    "name": "vac",
                    "chemical_symbols": ["vacancy"],
                    "concentration": [1.0],
                },
            ],
            "species_at_sites": ["Si", "Ge", "vac"],
            "assemblies": [
                {
                    "sites_in_groups": [[0], [1], [2]],
                    "group_probabilities": [0.3, 0.5, 0.2],
                }
            ],
            "structure_features": ["assemblies"],
        },
    }
