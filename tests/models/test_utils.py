from typing import Callable

import pytest
from pydantic import BaseModel, Field, ValidationError

from optimade.models.utils import OptimadeField, StrictField, SupportLevel


def make_bad_models(field: Callable):
    """Check that models using `field` to replace `Field` provide
    appropriate warnings and errors.

    """
    with pytest.raises(RuntimeError, match="with forbidden keywords"):

        class BadModel(BaseModel):
            bad_field: int = field(..., random_key="disallowed")

    with pytest.warns(UserWarning, match="No description"):

        class AnotherBadModel(BaseModel):
            bad_field: int = field(...)


def test_strict_field():
    """Test `StrictField` creation for failure on bad keys, and
    warnings with no description.

    """
    make_bad_models(StrictField)


def test_optimade_field():
    """Test `OptimadeField` creation for failure on bad keys, and
    warnings with no description.

    """
    make_bad_models(OptimadeField)


def test_compatible_strict_optimade_field() -> None:
    """This test checks that OptimadeField and StrictField
    produce the same schemas when given the same arguments.

    """
    from optimade.models.utils import (
        OPTIMADE_SCHEMA_EXTENSION_KEYS,
        OPTIMADE_SCHEMA_EXTENSION_PREFIX,
    )

    class CorrectModelWithStrictField(BaseModel):
        # check that unit and uniqueItems are passed through
        good_field: list[str] = StrictField(
            ...,
            support=SupportLevel.MUST,
            queryable=SupportLevel.OPTIONAL,
            description="Unit test to make sure that StrictField allows through OptimadeField keys",
            # pattern="^structures$",  # pattern is only allowed for string type
            unit="stringiness",
            uniqueItems=True,
            sortable=True,
        )

    class CorrectModelWithOptimadeField(BaseModel):
        good_field: list[str] = OptimadeField(
            ...,
            # Only difference here is that OptimadeField allows case-insensitive
            # strings to be passed instead of support levels directly
            support="must",
            queryable="optional",
            description="Unit test to make sure that StrictField allows through OptimadeField keys",
            # pattern="^structures$",  # pattern is only allowed for string type
            uniqueItems=True,
            unit="stringiness",
            sortable=True,
        )

    optimade_schema = CorrectModelWithOptimadeField.model_json_schema(mode="validation")
    strict_schema = CorrectModelWithStrictField.model_json_schema(mode="validation")
    strict_schema["title"] = optimade_schema["title"]
    assert strict_schema == optimade_schema

    assert "uniqueItems" in strict_schema["properties"]["good_field"]
    assert (
        "uniqueItems"
        in CorrectModelWithStrictField.model_fields["good_field"].json_schema_extra
    )

    for key in OPTIMADE_SCHEMA_EXTENSION_KEYS:
        assert key not in strict_schema["properties"]["good_field"]
        assert (
            f"{OPTIMADE_SCHEMA_EXTENSION_PREFIX}{key}"
            in CorrectModelWithStrictField.model_fields["good_field"].json_schema_extra
        )
        assert (
            f"{OPTIMADE_SCHEMA_EXTENSION_PREFIX}{key}"
            in strict_schema["properties"]["good_field"]
        )


def test_formula_regexp() -> None:
    """This test checks some simple chemical formulae with the
    `CHEMICAL_FORMULA_REGEXP`.

    """
    import re

    from optimade.models.utils import CHEMICAL_FORMULA_REGEXP

    class DummyModel(BaseModel):
        formula: str = Field(pattern=CHEMICAL_FORMULA_REGEXP)

    good_formulae = (
        "AgCl",
        "H5F",
        "LiP5",
        "Jn7Qb4",  # Regexp does not care about the actual existence of elements
        "A5B213CeD3E65F12G",
        "",
    )

    bad_formulae = (
        "Ag...Cl",
        "123123",
        "Ag   Cl",
        "abcd",
        "6F7G",
        "A0Be2",
        "A1Be2",
        "A0B1",
    )

    for formula in good_formulae:
        assert re.match(CHEMICAL_FORMULA_REGEXP, formula)
        assert DummyModel(formula=formula)

    for formula in bad_formulae:
        with pytest.raises(ValidationError):
            assert DummyModel(formula=formula)


def test_reduce_formula():
    from optimade.models.utils import reduce_formula

    assert reduce_formula("Si1O2") == "O2Si"
    assert reduce_formula("Si11O2") == "O2Si11"
    assert reduce_formula("Si10O2C4") == "C2OSi5"
    assert reduce_formula("Li1") == "Li"
    assert reduce_formula("Li1Ge1") == "GeLi"


def test_anonymize_formula():
    from optimade.models.utils import anonymize_formula

    assert anonymize_formula("Si1O2") == "A2B"
    assert anonymize_formula("Si11O2") == "A11B2"
    assert anonymize_formula("Si10O2C4") == "A5B2C"

    assert anonymize_formula("Si1 O2") == "A2B"
    assert anonymize_formula("Si11 O2") == "A11B2"
    assert anonymize_formula("Si10 O2C4") == "A5B2C"
