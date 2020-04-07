# pylint: disable=import-error
import json
from pathlib import Path
import re
from typing import List

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
from optimade.adapters.structures.proteindatabank import get_pdbx_mmcif


with open(Path(__file__).parent.joinpath("raw_test_structures.json"), "r") as raw_data:
    RAW_STRUCTURES: List[dict] = json.load(raw_data)


def test_successful_conversion():
    """Make sure its possible to convert"""
    for structure in RAW_STRUCTURES:
        # assert isinstance(get_pdbx_mmcif(Structure(structure)), str)
        with pytest.raises(NotImplementedError) as exc:
            get_pdbx_mmcif(Structure(structure))
        assert (
            str(exc.value)
            == "As of yet not implemented properly. Please use get_pdb instead."
        )


@pytest.mark.skip("PDFx/mmCIF has yet to be implemented.")
def test_special_species():
    """Make sure vacancies and non-chemical symbols ("X") are handled"""
    with open(Path(__file__).parent.joinpath("special_species.json"), "r") as raw_data:
        special_structures: List[dict] = json.load(raw_data)

    for special_structure in special_structures:
        structure = Structure(special_structure)

        assert isinstance(get_pdbx_mmcif(structure), str)
