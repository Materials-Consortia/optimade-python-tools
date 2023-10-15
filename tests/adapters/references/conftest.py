from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Any

    from optimade.adapters.references import Reference


@pytest.fixture
def RAW_REFERENCES() -> "list[dict[str, Any]]":
    """Read and return raw_references.json"""
    import json
    from pathlib import Path

    return json.loads(
        Path(__file__).parent.joinpath("raw_test_references.json").read_bytes()
    )


@pytest.fixture
def raw_reference(RAW_REFERENCES: "list[dict[str, Any]]") -> "dict[str, Any]":
    """Return random raw reference from raw_references.json"""
    from random import choice

    return choice(RAW_REFERENCES)


@pytest.fixture
def reference(raw_reference: "dict[str, Any]") -> "Reference":
    """Create and return adapters.Reference"""
    from optimade.adapters.references import Reference

    return Reference(raw_reference)
