# pylint: disable=import-error
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

from optimade.adapters import Structure
from optimade.adapters.exceptions import ConversionError
from optimade.adapters.structures.ase import get_ase_atoms


def test_successful_conversion(RAW_STRUCTURES):
    """Make sure its possible to convert"""
    for structure in RAW_STRUCTURES:
        assert isinstance(get_ase_atoms(Structure(structure)), Atoms)


def test_null_lattice_vectors(null_lattice_vector_structure):
    """Make sure null lattice vectors are handled"""
    assert isinstance(get_ase_atoms(null_lattice_vector_structure), Atoms)


def test_special_species(SPECIAL_SPECIES_STRUCTURES):
    """Make sure vacancies and non-chemical symbols ("X") are handled"""
    for special_structure in SPECIAL_SPECIES_STRUCTURES:
        structure = Structure(special_structure)

        with pytest.raises(
            ConversionError,
            match=r"(ASE cannot handle structures with partial occupancies)|"
            r"(ASE cannot handle structures with unknown \('X'\) chemical symbols)",
        ):
            get_ase_atoms(structure)


def test_null_species(null_species_structure):
    """Make sure null species are handled"""
    assert isinstance(get_ase_atoms(null_species_structure), Atoms)


def test_extra_info_keys(RAW_STRUCTURES):
    """Test that provider fields/ASE metadata is preserved during conversion."""
    structure = RAW_STRUCTURES[0]
    structure["attributes"]["_ase_key"] = "some value"
    structure["attributes"]["_ase_another_key"] = [1, 2, 3]
    structure["attributes"]["_key_without_ase_prefix"] = [4, 5, 6]

    atoms = Structure(structure).as_ase
    assert atoms.info["key"] == "some value"
    assert atoms.info["another_key"] == [1, 2, 3]
    assert atoms.info["_key_without_ase_prefix"] == [4, 5, 6]

    roundtrip_structure = Structure.ingest_from(atoms).attributes.dict()
    assert roundtrip_structure["_ase_key"] == "some value"
    assert roundtrip_structure["_ase_another_key"] == [1, 2, 3]

    # This key should have the _ase prefix re-added
    assert roundtrip_structure["_ase__key_without_ase_prefix"] == [4, 5, 6]
