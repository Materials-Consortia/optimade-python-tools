# pylint: disable=import-error

import pytest

from .utils import get_min_ver

min_ver = get_min_ver("aiida-core")
aiida = pytest.importorskip(
    "aiida",
    minversion=min_ver,
    reason=f"aiida-core must be installed with minimum version {min_ver} for these tests to"
    " be able to run",
)

from aiida import load_profile

load_profile()

from aiida.orm import StructureData

from optimade.adapters import Structure
from optimade.adapters.structures.aiida import get_aiida_structure_data


def test_successful_conversion(RAW_STRUCTURES):
    """Make sure its possible to convert"""
    for structure in RAW_STRUCTURES:
        assert isinstance(get_aiida_structure_data(Structure(structure)), StructureData)


def test_null_positions(null_position_structure):
    """Make sure null positions are handled"""
    assert isinstance(get_aiida_structure_data(null_position_structure), StructureData)


def test_null_lattice_vectors(null_lattice_vector_structure):
    """Make sure null lattice vectors are handled"""
    assert isinstance(
        get_aiida_structure_data(null_lattice_vector_structure), StructureData
    )


def test_special_species(SPECIAL_SPECIES_STRUCTURES):
    """Make sure vacancies and non-chemical symbols ("X") are handled"""
    for special_structure in SPECIAL_SPECIES_STRUCTURES:
        structure = Structure(special_structure)

        aiida_structure = get_aiida_structure_data(structure)

        assert isinstance(aiida_structure, StructureData)

        if "vacancy" in structure.attributes.species[0].chemical_symbols:
            assert aiida_structure.has_vacancies
            assert not aiida_structure.is_alloy
        elif len(structure.attributes.species[0].chemical_symbols) > 1:
            assert not aiida_structure.has_vacancies
            assert aiida_structure.is_alloy
        else:
            assert not aiida_structure.has_vacancies
            assert not aiida_structure.is_alloy
