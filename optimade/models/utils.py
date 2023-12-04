import inspect
import itertools
import math
import re
import warnings
from enum import Enum
from functools import reduce
from typing import TYPE_CHECKING, Any, Optional, Union

from pydantic import Field
from pydantic_core import PydanticUndefined

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Generator

_PYDANTIC_FIELD_KWARGS = list(inspect.signature(Field).parameters.keys())

__all__ = (
    "CHEMICAL_SYMBOLS",
    "EXTRA_SYMBOLS",
    "ATOMIC_NUMBERS",
    "SupportLevel",
)

OPTIMADE_SCHEMA_EXTENSION_KEYS = ["support", "queryable", "unit", "sortable"]
OPTIMADE_SCHEMA_EXTENSION_PREFIX = "x-optimade-"

SEMVER_PATTERN = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"


class SupportLevel(Enum):
    """OPTIMADE property/field support levels"""

    MUST = "must"
    SHOULD = "should"
    OPTIONAL = "optional"


def StrictField(
    default: "Any" = PydanticUndefined,
    *,
    description: Optional[str] = None,
    **kwargs: "Any",
) -> Any:
    """A wrapper around `pydantic.Field` that does the following:

    - Forbids any "extra" keys that would be passed to `pydantic.Field`,
      except those used elsewhere to modify the schema in-place,
      e.g. "uniqueItems", "pattern" and those added by OptimadeField, e.g.
      "unit", "queryable" and "sortable".
    - Emits a warning when no description is provided.

    Arguments:
        default: The only non-keyword argument allowed for Field.
        description: The description of the `Field`; if this is not
            specified then a `UserWarning` will be emitted.
        **kwargs: Extra keyword arguments to be passed to `Field`.

    Raises:
        RuntimeError: If `**kwargs` contains a key not found in the
            function signature of `Field`, or in the extensions used
            by models in this package (see above).

    Returns:
        The pydantic `Field`.

    """
    allowed_schema_and_field_keys = ["pattern"]

    allowed_keys = [
        "pattern",
        "uniqueItems",
    ] + OPTIMADE_SCHEMA_EXTENSION_KEYS
    _banned = [k for k in kwargs if k not in set(_PYDANTIC_FIELD_KWARGS + allowed_keys)]

    if _banned:
        raise RuntimeError(
            f"Not creating StrictField({default!r}, **{kwargs!r}) with "
            f"forbidden keywords {_banned}."
        )

    # Handle description
    if description is None:
        warnings.warn(
            f"No description provided for StrictField specified by {default!r}, "
            f"**{kwargs!r}."
        )
    else:
        kwargs["description"] = description

    # OPTIMADE schema extensions
    json_schema_extra: dict[str, Any] = kwargs.pop("json_schema_extra", {})

    # Go through all JSON Schema keys and add them to the json_schema_extra.
    for key in allowed_keys:
        if key not in kwargs:
            continue

        # If they are OPTIMADE schema extensions, add them with the OPTIMADE prefix.
        schema_key = (
            f"{OPTIMADE_SCHEMA_EXTENSION_PREFIX}{key}"
            if key in OPTIMADE_SCHEMA_EXTENSION_KEYS
            else key
        )

        for key_variant in (key, schema_key):
            if key_variant in json_schema_extra:
                if json_schema_extra.pop(key_variant) != kwargs[key]:
                    raise RuntimeError(
                        f"Conflicting values for {key} in json_schema_extra and kwargs."
                    )

        json_schema_extra[schema_key] = (
            kwargs[key] if key in allowed_schema_and_field_keys else kwargs.pop(key)
        )

    kwargs["json_schema_extra"] = json_schema_extra

    return Field(default, **kwargs)


def OptimadeField(
    default: "Any" = PydanticUndefined,
    *,
    support: Optional[Union[str, SupportLevel]] = None,
    queryable: Optional[Union[str, SupportLevel]] = None,
    unit: Optional[str] = None,
    **kwargs,
) -> Any:
    """A wrapper around `pydantic.Field` that adds OPTIMADE-specific
    field paramters `queryable`, `support` and `unit`, indicating
    the corresponding support level in the specification and the
    physical unit of the field.

    Arguments:
        support: The support level of the field itself, i.e. whether the field
            can be null or omitted by an implementation.
        queryable: The support level corresponding to the queryablility
            of this field.
        unit: A string describing the unit of the field.

    Returns:
        The pydantic field with extra validation provided by [`StrictField`][optimade.models.utils.StrictField].

    """

    # Collect non-null keyword arguments to add to the Field schema
    if unit is not None:
        kwargs["unit"] = unit

    if queryable is not None:
        if isinstance(queryable, str):
            queryable = SupportLevel(queryable.lower())
        kwargs["queryable"] = queryable

    if support is not None:
        if isinstance(support, str):
            support = SupportLevel(support.lower())
        kwargs["support"] = support

    return StrictField(default, **kwargs)


def anonymous_element_generator() -> "Generator[str, None, None]":
    """Generator that yields the next symbol in the A, B, Aa, ... Az naming scheme."""
    from string import ascii_lowercase

    for size in itertools.count(1):
        for tuple_strings in itertools.product(ascii_lowercase, repeat=size):
            list_strings = list(tuple_strings)
            list_strings[0] = list_strings[0].upper()
            yield "".join(list_strings)


def _reduce_or_anonymize_formula(
    formula: str, alphabetize: bool = True, anonymize: bool = False
) -> str:
    """Takes an input formula, reduces it and either alphabetizes or anonymizes it."""
    import sys

    numbers: list[int] = [
        int(n.strip() or 1) for n in re.split(r"[A-Z][a-z]*", formula)[1:]
    ]
    # Need to remove leading 1 from split and convert to ints

    species: list[str] = re.findall("[A-Z][a-z]*", formula)

    if sys.version_info[1] >= 9:
        gcd = math.gcd(*numbers)
    else:
        gcd = reduce(math.gcd, numbers)

    if not len(species) == len(numbers):
        raise ValueError(f"Something is wrong with the input formula: {formula}")

    numbers = [n // gcd for n in numbers]

    if anonymize:
        numbers = sorted(numbers, reverse=True)
        species = [s for _, s in zip(numbers, anonymous_element_generator())]

    elif alphabetize:
        species, numbers = zip(*sorted(zip(species, numbers)))  # type: ignore[assignment]

    return "".join(f"{s}{n if n != 1 else ''}" for n, s in zip(numbers, species))


def anonymize_formula(formula: str) -> str:
    """Takes a string representation of a chemical formula of the form `[A-Z][a-z]*[0-9]*` (potentially with whitespace) and
    returns the OPTIMADE `chemical_formula_anonymous` representation, i.e., a reduced chemical formula comprising of element symbols
    drawn from A, B, C... ordered from largest proportion to smallest.

    Returns:
        The anonymous chemical formula in the OPTIMADE representation.

    """
    return _reduce_or_anonymize_formula(formula, alphabetize=False, anonymize=True)


def reduce_formula(formula: str) -> str:
    """Takes a string representation of a chemical formula of the form `[A-Z][a-z]*[0-9]*` (potentially with whitespace) and
    reduces it by the GCD of the proportion integers present in the formula, stripping any leftover "1" values.

    Returns:
        The reduced chemical formula in the OPTIMADE representation.

    """
    return _reduce_or_anonymize_formula(formula, alphabetize=True, anonymize=False)


ANONYMOUS_ELEMENTS = tuple(itertools.islice(anonymous_element_generator(), 150))
""" Returns the first 150 values of the anonymous element generator. """

CHEMICAL_FORMULA_REGEXP = r"(^$)|^([A-Z][a-z]?([2-9]|[1-9]\d+)?)+$"

EXTRA_SYMBOLS = ["X", "vacancy"]

CHEMICAL_SYMBOLS = [
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Fr",
    "Ra",
    "Ac",
    "Th",
    "Pa",
    "U",
    "Np",
    "Pu",
    "Am",
    "Cm",
    "Bk",
    "Cf",
    "Es",
    "Fm",
    "Md",
    "No",
    "Lr",
    "Rf",
    "Db",
    "Sg",
    "Bh",
    "Hs",
    "Mt",
    "Ds",
    "Rg",
    "Cn",
    "Nh",
    "Fl",
    "Mc",
    "Lv",
    "Ts",
    "Og",
]

ATOMIC_NUMBERS = {}
for Z, symbol in enumerate(CHEMICAL_SYMBOLS):
    ATOMIC_NUMBERS[symbol] = Z + 1

EXTENDED_CHEMICAL_SYMBOLS_PATTERN = (
    "(" + "|".join(CHEMICAL_SYMBOLS + EXTRA_SYMBOLS) + ")"
)

ELEMENT_SYMBOLS_PATTERN = "(" + "|".join(CHEMICAL_SYMBOLS) + ")"
