# pylint: disable=import-error
import json
from pathlib import Path
import re
from typing import List

import pytest

from .utils import get_min_ver

min_ver = get_min_ver("pymatgen")
pymatgen = pytest.importorskip(
    "pymatgen",
    minversion=min_ver,
    reason=f"pymatgen must be installed with minimum version {min_ver} for these tests to"
    " be able to run",
)

from pymatgen import Molecule, Structure as PymatgenStructure

from optimade.models.structures import Periodicity

from optimade.adapters import Structure
from optimade.adapters.exceptions import ConversionError
from optimade.adapters.structures.pymatgen import (
    get_pymatgen,
    _get_structure,
    _get_molecule,
)


with open(Path(__file__).parent.joinpath("raw_test_structures.json"), "r") as raw_data:
    RAW_STRUCTURES: List[dict] = json.load(raw_data)


def test_successful_conversion():
    """Make sure its possible to convert"""
    for structure in RAW_STRUCTURES:
        assert isinstance(
            get_pymatgen(Structure(structure)), (PymatgenStructure, Molecule)
        )


def test_successful_conversion_structure():
    """Make sure its possible to convert to pymatgen Structure"""
    structure = Structure(RAW_STRUCTURES[0])
    structure.attributes.dimension_types = (Periodicity.PERIODIC,) * 3
    structure.attributes.lattice_vectors = (
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    assert isinstance(_get_structure(structure), PymatgenStructure)
    assert isinstance(get_pymatgen(structure), PymatgenStructure)


def test_successful_conversion_molecule():
    """Make sure its possible to convert to pymatgen Molecule"""
    structure = Structure(RAW_STRUCTURES[0])
    structure.attributes.dimension_types = (
        Periodicity.PERIODIC,
        Periodicity.PERIODIC,
        Periodicity.APERIODIC,
    )
    structure.attributes.lattice_vectors = (
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 0.0),
    )
    assert isinstance(_get_molecule(structure), Molecule)
    assert isinstance(get_pymatgen(structure), Molecule)


def test_null_positions():
    """Make sure null positions are handled"""
    structure = Structure(RAW_STRUCTURES[0])
    structure.attributes.cartesian_site_positions[0] = (None,) * 3
    with pytest.raises(ConversionError) as exc:
        get_pymatgen(structure)
    assert (
        "pymatgen cannot be used to convert structures with unknown positions."
        == str(exc.value)
    )


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
    assert isinstance(_get_molecule(structure), Molecule)
    assert isinstance(get_pymatgen(structure), Molecule)
