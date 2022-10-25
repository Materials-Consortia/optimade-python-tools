from typing import Callable, List

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


def test_compatible_strict_optimade_field():
    """This test checks that OptimadeField and StrictField
    produce the same schemas when given the same arguments.

    """

    class CorrectModelWithStrictField(BaseModel):
        # check that unit and uniqueItems are passed through
        good_field: List[str] = StrictField(
            ...,
            support=SupportLevel.MUST,
            queryable=SupportLevel.OPTIONAL,
            description="Unit test to make sure that StrictField allows through OptimadeField keys",
            pattern="^structures$",
            unit="stringiness",
            uniqueItems=True,
            sortable=True,
        )

    class CorrectModelWithOptimadeField(BaseModel):

        good_field: List[str] = OptimadeField(
            ...,
            # Only difference here is that OptimadeField allows case-insensitive
            # strings to be passed instead of support levels directly
            support="must",
            queryable="optional",
            description="Unit test to make sure that StrictField allows through OptimadeField keys",
            pattern="^structures$",
            uniqueItems=True,
            unit="stringiness",
            sortable=True,
        )

    optimade_schema = CorrectModelWithOptimadeField.schema()
    strict_schema = CorrectModelWithStrictField.schema()
    strict_schema["title"] = optimade_schema["title"]
    assert strict_schema == optimade_schema


def test_formula_regexp():
    """This test checks some simple chemical formulae with the
    `CHEMICAL_FORMULA_REGEXP`.

    """
    import re

    from optimade.models.utils import CHEMICAL_FORMULA_REGEXP

    class DummyModel(BaseModel):
        formula: str = Field(regex=CHEMICAL_FORMULA_REGEXP)

    good_formulae = (
        "AgCl",
        "H5F",
        "LiP5",
        "Jn7Qb4",  # Regexp does not care about the actual existence of elements
        "A5B213CeD3E65F12G",
    )

    bad_formulae = (
        "Ag...Cl",
        "123123",
        "Ag   Cl",
        "abcd",
        "6F7G",
        "A0Be2",
        "A1Be2",
        "",
    )

    for formula in good_formulae:
        assert re.match(CHEMICAL_FORMULA_REGEXP, formula)
        assert DummyModel(formula=formula)

    for formula in bad_formulae:
        with pytest.raises(ValidationError):
            assert DummyModel(formula=formula)
