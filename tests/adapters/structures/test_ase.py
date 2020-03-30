# pylint: disable=import-error
import json
from pathlib import Path
import re
from typing import List

import pytest

from .utils import get_min_ver

min_ver = get_min_ver("ase")
ase = pytest.importorskip(
    "ase",
    minversion=min_ver,
    reason=f"ase must be installed with minimum version {min_ver} for these tests to"
    " be able to run",
)

from ase import Atoms

from optimade.models.structures import Periodicity

from optimade.adapters import Structure
from optimade.adapters.structures.ase import get_ase_atoms


with open(Path(__file__).parent.joinpath("raw_test_structures.json"), "r") as raw_data:
    RAW_STRUCTURES: List[dict] = json.load(raw_data)


def test_successful_conversion():
    """Make sure its possible to convert"""
    for structure in RAW_STRUCTURES:
        assert isinstance(get_ase_atoms(Structure(structure)), Atoms)


def test_null_positions():
    """Make sure null positions are handled"""
    structure = Structure(RAW_STRUCTURES[0])
    structure.attributes.cartesian_site_positions[0] = (None,) * 3
    assert isinstance(get_ase_atoms(structure), Atoms)


def test_null_lattice_vectors():
    """Make sure null lattice vectors are handled"""
    structure = Structure(RAW_STRUCTURES[0])
    structure.attributes.dimension_types = (
        Periodicity.PERIODIC,
        Periodicity.PERIODIC,
        Periodicity.APERIODIC,
    )
    structure.attributes.lattice_vectors = (
        (None, None, None),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    assert isinstance(get_ase_atoms(structure), Atoms)
