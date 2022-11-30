# pylint: disable=import-error
import pytest

from .utils import get_min_ver

min_ver = get_min_ver("pymatgen")
pymatgen = pytest.importorskip(
    "pymatgen.core",
    minversion=min_ver,
    reason=f"pymatgen must be installed with minimum version {min_ver} for these tests to"
    " be able to run",
)

from pymatgen.core import Molecule
from pymatgen.core import Structure as PymatgenStructure

from optimade.adapters import Structure
from optimade.adapters.structures.pymatgen import (
    _get_molecule,
    _get_structure,
    from_pymatgen,
    get_pymatgen,
)


def test_successful_conversion(RAW_STRUCTURES):
    """Make sure its possible to convert"""
    for structure in RAW_STRUCTURES:
        assert isinstance(
            get_pymatgen(Structure(structure)), (PymatgenStructure, Molecule)
        )


def test_successful_conversion_structure(structure):
    """Make sure its possible to convert to pymatgen Structure"""
    assert isinstance(_get_structure(structure), PymatgenStructure)
    assert isinstance(get_pymatgen(structure), PymatgenStructure)


def test_null_lattice_vectors(null_lattice_vector_structure):
    """Make sure null lattice vectors are handled

    This also respresents a test for successful conversion to pymatgen Molecule
    """
    assert isinstance(_get_molecule(null_lattice_vector_structure), Molecule)
    assert isinstance(get_pymatgen(null_lattice_vector_structure), Molecule)


def test_special_species(SPECIAL_SPECIES_STRUCTURES):
    """Make sure vacancies and non-chemical symbols ("X") are handled"""
    for special_structure in SPECIAL_SPECIES_STRUCTURES:
        structure = Structure(special_structure)
        assert isinstance(get_pymatgen(structure), PymatgenStructure)


def test_null_species(null_species_structure):
    """Make sure null species are handled"""
    assert isinstance(get_pymatgen(null_species_structure), PymatgenStructure)


def test_successful_ingestion(RAW_STRUCTURES):
    import numpy as np

    lossy_keys = (
        "chemical_formula_descriptive",
        "chemical_formula_hill",
        "last_modified",
        "assemblies",
        "attached",
        "immutable_id",
        "species",
        "fractional_site_positions",
    )
    array_keys = ("cartesian_site_positions", "lattice_vectors")
    for structure in RAW_STRUCTURES:
        converted = from_pymatgen(get_pymatgen(Structure(structure))).dict()
        for k in converted:
            if k not in lossy_keys:
                if k in array_keys:
                    np.testing.assert_almost_equal(
                        converted[k], structure["attributes"][k]
                    )
                else:
                    assert converted[k] == structure["attributes"][k]
