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


with open(Path(__file__).parent.joinpath("raw_test_structures.json"), "r") as raw_data:
    RAW_STRUCTURES: List[dict] = json.load(raw_data)


def test_successful_conversion():
    """Make sure its possible to convert"""
    for structure in RAW_STRUCTURES:
        assert isinstance(get_aiida_structure_data(Structure(structure)), StructureData)


def test_null_positions():
    """Make sure null positions are handled"""
    structure = Structure(RAW_STRUCTURES[0])
    structure.attributes.cartesian_site_positions[0] = (None,) * 3
    with pytest.raises(ConversionError) as exc:
        get_aiida_structure_data(structure)
    assert "AiiDA cannot be used to convert structures with unknown positions." == str(
        exc.value
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
    assert isinstance(get_aiida_structure_data(structure), StructureData)
    assert get_aiida_structure_data(structure).cell[0] != [
        1.0,
        1.0,
        1.0,
    ], "The cell should have been adjusted to not anymore start with (1.0, 1.0, 1.0), which it converts all None values to."


def test_special_species():
    """Make sure vacancies and non-chemical symbols ("X") are handled"""
    with open(Path(__file__).parent.joinpath("special_species.json"), "r") as raw_data:
        special_structures: List[dict] = json.load(raw_data)

    for special_structure in special_structures:
        structure = Structure(special_structure)

        assert isinstance(get_aiida_structure_data(structure), StructureData)

        if "vacancy" in structure.attributes.species[0].chemical_symbols:
            assert get_aiida_structure_data(structure).has_vacancies
            assert not get_aiida_structure_data(structure).is_alloy
        else:
            assert not get_aiida_structure_data(structure).has_vacancies
            assert get_aiida_structure_data(structure).is_alloy
