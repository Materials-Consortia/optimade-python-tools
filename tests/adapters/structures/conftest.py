import json
from pathlib import Path
from random import choice
from typing import List

import pytest

from optimade.adapters.structures import Structure


@pytest.fixture
def RAW_STRUCTURES() -> List[dict]:
    """Read and return raw_structures.json"""
    with open(
        Path(__file__).parent.joinpath("raw_test_structures.json"), "r"
    ) as raw_data:
        return json.load(raw_data)


@pytest.fixture
def SPECIAL_SPECIES_STRUCTURES() -> List[dict]:
    """Read and return special_species.json"""
    with open(Path(__file__).parent.joinpath("special_species.json"), "r") as raw_data:
        return json.load(raw_data)


@pytest.fixture
def raw_structure(RAW_STRUCTURES) -> dict:
    """Return random raw structure from raw_structures.json"""
    return choice(RAW_STRUCTURES)


@pytest.fixture
def structure(raw_structure) -> Structure:
    """Create and return adapters.Structure"""
    return Structure(raw_structure)


@pytest.fixture
def structures(RAW_STRUCTURES) -> List[Structure]:
    """Create and return list of adapters.Structure"""
    return [Structure(_) for _ in RAW_STRUCTURES]


@pytest.fixture
def null_lattice_vector_structure(raw_structure) -> Structure:
    """Create and return adapters.Structure with lattice_vectors that have None values"""
    raw_structure["attributes"]["lattice_vectors"][0] = [None] * 3
    raw_structure["attributes"]["dimension_types"][0] = 0
    raw_structure["attributes"]["nperiodic_dimensions"] = 2
    return Structure(raw_structure)
