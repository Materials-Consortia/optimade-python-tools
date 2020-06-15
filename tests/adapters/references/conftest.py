import json
from pathlib import Path
from random import choice

import pytest

from optimade.adapters.references import Reference


@pytest.fixture
def RAW_REFERENCES():
    """Read and return raw_references.json"""
    with open(
        Path(__file__).parent.joinpath("raw_test_references.json"), "r"
    ) as raw_data:
        return json.load(raw_data)


@pytest.fixture
def raw_reference(RAW_REFERENCES):
    """Return random raw reference from raw_references.json"""
    return choice(RAW_REFERENCES)


@pytest.fixture
def reference(raw_reference):
    """Create and return adapters.Reference"""
    return Reference(raw_reference)
