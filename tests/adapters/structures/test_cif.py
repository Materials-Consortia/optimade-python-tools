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
from optimade.adapters.structures.cif import get_cif


with open(Path(__file__).parent.joinpath("raw_test_structures.json"), "r") as raw_data:
    RAW_STRUCTURES: List[dict] = json.load(raw_data)


def test_successful_conversion():
    """Make sure its possible to convert"""
    for structure in RAW_STRUCTURES:
        assert isinstance(get_cif(Structure(structure)), str)
