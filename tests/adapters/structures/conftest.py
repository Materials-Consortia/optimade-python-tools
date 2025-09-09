from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Any

    from optimade.adapters.structures import Structure


@pytest.fixture
def RAW_STRUCTURES() -> "list[dict[str, Any]]":
    """Read and return raw_structures.json"""
    import json
    from pathlib import Path

    return json.loads(
        Path(__file__).parent.joinpath("raw_test_structures.json").read_bytes()
    )


@pytest.fixture
def SPECIAL_SPECIES_STRUCTURES() -> "list[dict[str, Any]]":
    """Read and return special_species.json"""
    import json
    from pathlib import Path

    return json.loads(
        Path(__file__).parent.joinpath("special_species.json").read_bytes()
    )


@pytest.fixture
def raw_structure(RAW_STRUCTURES: "list[dict[str, Any]]") -> "dict[str, Any]":
    """Return random raw structure from raw_structures.json"""
    from random import choice

    return choice(RAW_STRUCTURES)


@pytest.fixture
def structure(raw_structure: "dict[str, Any]") -> "Structure":
    """Create and return adapters.Structure"""
    from optimade.adapters.structures import Structure

    return Structure(raw_structure)


@pytest.fixture
def structures(RAW_STRUCTURES: "list[dict[str, Any]]") -> "list[Structure]":
    """Create and return list of adapters.Structure"""
    from optimade.adapters.structures import Structure

    return [Structure(_) for _ in RAW_STRUCTURES]


@pytest.fixture
def null_lattice_vector_structure(raw_structure: "dict[str, Any]") -> "Structure":
    """Create and return adapters.Structure with lattice_vectors that have None values"""
    from optimade.adapters.structures import Structure

    raw_structure["attributes"]["lattice_vectors"][0] = [None] * 3
    raw_structure["attributes"]["dimension_types"][0] = 0
    raw_structure["attributes"]["nperiodic_dimensions"] = sum(
        raw_structure["attributes"]["dimension_types"]
    )
    return Structure(raw_structure)


@pytest.fixture
def null_species_structure(raw_structure: "dict[str, Any]") -> "Structure":
    """Create and return Structure with species that have None values"""
    from optimade.adapters.structures import Structure

    raw_structure["attributes"]["species"] = None
    return Structure(raw_structure)
