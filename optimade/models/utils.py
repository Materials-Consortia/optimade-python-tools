from typing import cast, Any, Dict, Type
from pydantic import ConstrainedInt, errors
from pydantic.types import OptionalInt
from pydantic.validators import list_validator


__all__ = ("NonnegativeInt", "CHEMICAL_SYMBOLS", "EXTRA_SYMBOLS", "ATOMIC_NUMBERS")


class NonnegativeInt(ConstrainedInt):
    ge = 0


class ConstrainedListMeta(type):
    def __new__(
        cls, name: str, bases: Any, dct: Dict[str, Any]
    ) -> "ConstrainedList":  # noqa
        new_cls = cast("ConstrainedList", type.__new__(cls, name, bases, dct))

        if new_cls.len_gt is not None and new_cls.len_ge is not None:
            raise errors.ConfigError(
                "bounds len_gt and len_ge cannot be specified at the same time"
            )
        if new_cls.len_lt is not None and new_cls.len_le is not None:
            raise errors.ConfigError(
                "bounds len_lt and len_le cannot be specified at the same time"
            )
        if new_cls.len_eq is not None and any(
            v is not None
            for v in (new_cls.len_gt, new_cls.len_ge, new_cls.len_lt, new_cls.len_le)
        ):
            raise errors.ConfigError(
                "len_eq cannot be specified at the same time as any other constraint"
            )
        return new_cls


def list_length_validator(v: "List", field: "Field") -> "List":  # noqa
    field_type: ConstrainedList = field.type_  # type: ignore
    if field_type.len_gt is not None and not len(v) > field_type.len_gt:
        raise errors.NumberNotGtError(limit_value=field_type.len_gt)
    if field_type.len_ge is not None and not len(v) >= field_type.len_ge:
        raise errors.NumberNotGeError(limit_value=field_type.len_ge)
    if field_type.len_lt is not None and not len(v) < field_type.len_lt:
        raise errors.NumberNotLtError(limit_value=field_type.len_lt)
    if field_type.len_le is not None and not len(v) <= field_type.len_le:
        raise errors.NumberNotLeError(limit_value=field_type.len_le)
    if field_type.len_eq is not None and not len(v) == field_type.len_eq:
        raise errors.NumberNotLeError(limit_value=field_type.len_eq)

    return v


class ConstrainedList(list, metaclass=ConstrainedListMeta):
    len_gt: OptionalInt = None
    len_ge: OptionalInt = None
    len_lt: OptionalInt = None
    len_le: OptionalInt = None
    len_eq: OptionalInt = None

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":  # noqa
        yield list_validator
        yield list_length_validator


def conlist(
    *,
    len_gt: int = None,
    len_ge: int = None,
    len_lt: int = None,
    len_le: int = None,
    len_eq: int = None
) -> Type[list]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(
        len_gt=len_gt, len_ge=len_ge, len_lt=len_lt, len_le=len_le, len_eq=len_eq
    )
    return type("ConstrainedListValue", (ConstrainedList,), namespace)


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
