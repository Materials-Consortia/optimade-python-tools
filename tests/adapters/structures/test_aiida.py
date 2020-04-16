# pylint: disable=import-error
import json
from pathlib import Path
import re
from typing import List

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

from optimade.models.structures import Periodicity

from optimade.adapters import Structure
from optimade.adapters.exceptions import ConversionError
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

        assert isinstance(get_aiida_structure_data(structure), StructureData)

        if "vacancy" in structure.attributes.species[0].chemical_symbols:
            assert get_aiida_structure_data(structure).has_vacancies
            assert not get_aiida_structure_data(structure).is_alloy
        else:
            assert not get_aiida_structure_data(structure).has_vacancies
            assert get_aiida_structure_data(structure).is_alloy
