# pylint: disable=import-error
import pytest

from .utils import get_min_ver

min_ver = get_min_ver("jarvis-tools")
jarvis = pytest.importorskip(
    "jarvis",
    minversion=min_ver,
    reason=f"jarvis-tools must be installed with minimum version {min_ver} for these tests to"
    " be able to run",
)

from jarvis.core.atoms import Atoms
from optimade.adapters import Structure
from optimade.adapters.exceptions import ConversionError
from optimade.adapters.structures.jarvis import get_jarvis_atoms


def test_successful_conversion(RAW_STRUCTURES):
    """Make sure its possible to convert"""
    for structure in RAW_STRUCTURES:
        assert isinstance(get_jarvis_atoms(Structure(structure)), Atoms)


def test_null_lattice_vectors(null_lattice_vector_structure):
    """Make sure null lattice vectors are handled"""
    assert isinstance(get_jarvis_atoms(null_lattice_vector_structure), Atoms)


def test_special_species(SPECIAL_SPECIES_STRUCTURES):
    """Make sure vacancies and non-chemical symbols ("X") are handled"""
    for special_structure in SPECIAL_SPECIES_STRUCTURES:
        structure = Structure(special_structure)

        # Since all the special species structure only have a single species, this works fine.
        if len(structure.species[0].chemical_symbols) > 1:
            # If the structure is disordered (has partial occupancies of any kind),
            # jarvis-tools cannot convert the structure
            with pytest.raises(
                ConversionError,
                match="jarvis-tools cannot handle structures with partial occupancies",
            ):
                get_jarvis_atoms(structure)
        else:
            # No partial occupancies, just special/non-standard species.
            # jarvis-tools should convert these structure fine enough.
            assert isinstance(get_jarvis_atoms(structure), Atoms)
