import inspect
import itertools
import math
import re
import warnings
from enum import Enum
from functools import reduce
from typing import Any, Dict, List, Optional, Union

from pydantic import Field

# from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

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


# class StrictFieldInfo(FieldInfo):
#     """Wraps the standard pydantic `FieldInfo` in order
#     to prefix any custom keys from `StrictField`.

#     """

#     def __init__(self, *args, **kwargs):
#         if not kwargs.get("default"):
#             kwargs["default"] = args[0] if args else None
#         super().__init__(**kwargs)
#         for key in OPTIMADE_SCHEMA_EXTENSION_KEYS:
#             if self.json_schema_extra and key in self.json_schema_extra:
#                 self.json_schema_extra[
#                     f"{OPTIMADE_SCHEMA_EXTENSION_PREFIX}{key}"
#                 ] = self.json_schema_extra.pop(key)


# def StrictPydanticField(*args, **kwargs):
#     """Wrapper for `Field` that uses `StrictFieldInfo` instead of
#     the pydantic `FieldInfo`.
#     """
#     field_info = StrictFieldInfo(*args, **kwargs)
#     return field_info


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

    allowed_keys = [
        "pattern",
        "uniqueItems",
        "nullable",
    ] + OPTIMADE_SCHEMA_EXTENSION_KEYS
    _banned = [k for k in kwargs if k not in set(_PYDANTIC_FIELD_KWARGS + allowed_keys)]

    if _banned:
        raise RuntimeError(
            f"Not creating StrictField({default!r}, **{kwargs!r}) with "
            f"forbidden keywords {_banned}."
        )

    if description is None:
        warnings.warn(
            f"No description provided for StrictField specified by {default!r}, "
            f"**{kwargs!r}."
        )
    else:
        kwargs["description"] = description

    # OPTIMADE schema extensions
    if "json_schema_extra" in kwargs:
        json_schema_extra: Dict[str, Any] = kwargs["json_schema_extra"]
        for key in OPTIMADE_SCHEMA_EXTENSION_KEYS:
            if key in list(kwargs["json_schema_extra"]):
                json_schema_extra[
                    f"{OPTIMADE_SCHEMA_EXTENSION_PREFIX}{key}"
                ] = json_schema_extra.pop(key)
        kwargs["json_schema_extra"] = json_schema_extra

    return Field(
        default,
        # default_factory=kwargs.pop("default_factory", PydanticUndefined),
        # alias=kwargs.pop("alias", PydanticUndefined),
        # alias_priority=kwargs.pop("alias_priority", PydanticUndefined),
        # validation_alias=kwargs.pop("validation_alias", PydanticUndefined),
        # serialization_alias=kwargs.pop("serialization_alias", PydanticUndefined),
        # title=kwargs.pop("title", PydanticUndefined),
        # description=kwargs.pop("description", PydanticUndefined),
        # examples=kwargs.pop("examples", PydanticUndefined),
        # exclude=kwargs.pop("exclude", PydanticUndefined),
        # discriminator=kwargs.pop("discriminator", PydanticUndefined),
        # json_schema_extra=kwargs.pop("json_schema_extra", PydanticUndefined),
        # frozen=kwargs.pop("frozen", PydanticUndefined),
        # validate_default=kwargs.pop("validate_default", PydanticUndefined),
        # repr=kwargs.pop("repr", PydanticUndefined),
        # init_var=kwargs.pop("init_var", PydanticUndefined),
        # kw_only=kwargs.pop("kw_only", PydanticUndefined),
        # pattern=kwargs.pop("pattern", PydanticUndefined),
        # strict=kwargs.pop("strict", PydanticUndefined),
        # gt=kwargs.pop("gt", PydanticUndefined),
        # ge=kwargs.pop("ge", PydanticUndefined),
        # lt=kwargs.pop("lt", PydanticUndefined),
        # le=kwargs.pop("le", PydanticUndefined),
        # multiple_of=kwargs.pop("multiple_of", PydanticUndefined),
        # allow_inf_nan=kwargs.pop("allow_inf_nan", PydanticUndefined),
        # max_digits=kwargs.pop("max_digits", PydanticUndefined),
        # decimal_places=kwargs.pop("decimal_places", PydanticUndefined),
        # min_length=kwargs.pop("min_length", PydanticUndefined),
        # max_length=kwargs.pop("max_length", PydanticUndefined),
        # union_mode=kwargs.pop("union_mode", PydanticUndefined),
        **kwargs,
    )


def OptimadeField(
    default: "Any" = PydanticUndefined,
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


def anonymous_element_generator():
    """Generator that yields the next symbol in the A, B, Aa, ... Az naming scheme."""
    from string import ascii_lowercase

    for size in itertools.count(1):
        for s in itertools.product(ascii_lowercase, repeat=size):
            s = list(s)
            s[0] = s[0].upper()
            yield "".join(s)


def _reduce_or_anonymize_formula(
    formula: str, alphabetize: bool = True, anonymize: bool = False
) -> str:
    """Takes an input formula, reduces it and either alphabetizes or anonymizes it."""
    import sys

    numbers: List[int] = [
        int(n.strip() or 1) for n in re.split(r"[A-Z][a-z]*", formula)[1:]
    ]
    # Need to remove leading 1 from split and convert to ints

    species = re.findall("[A-Z][a-z]*", formula)

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
        species, numbers = zip(*sorted(zip(species, numbers)))

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
