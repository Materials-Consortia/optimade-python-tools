import pytest

from .utils import get_min_ver

min_ver = get_min_ver("numpy")
numpy = pytest.importorskip(
    "numpy",
    minversion=min_ver,
    reason=f"numpy must be installed with minimum version {min_ver} for these tests to"
    " be able to run",
)

from optimade.adapters import Structure
from optimade.adapters.structures.cif import get_cif


def test_successful_conversion(RAW_STRUCTURES):
    """Make sure its possible to convert"""
    for structure in RAW_STRUCTURES:
        assert isinstance(get_cif(Structure(structure)), str)


def test_null_lattice_vectors(null_lattice_vector_structure):
    """Make sure null lattice vectors are handled"""
    assert isinstance(get_cif(null_lattice_vector_structure), str)


def test_special_species(SPECIAL_SPECIES_STRUCTURES):
    """Make sure vacancies and non-chemical symbols ("X") are handled"""
    for special_structure in SPECIAL_SPECIES_STRUCTURES:
        structure = Structure(special_structure)

        assert isinstance(get_cif(structure), str)
