import inspect
import itertools
import re
import warnings
from enum import Enum
from typing import TYPE_CHECKING, Optional, Union

from pydantic import Field
from pydantic.fields import FieldInfo

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any

class DataType(Enum):
    """Optimade Data Types

    See the section "Data types" in the OPTIMADE API specification for more information.
    """

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    LIST = "list"
    DICTIONARY = "dictionary"
    UNKNOWN = "unknown"

    @classmethod
    def get_values(cls):
        """Get OPTIMADE data types (enum values) as a (sorted) list"""
        return sorted((_.value for _ in cls))

    @classmethod
    def from_python_type(cls, python_type: Union[type, str, object]):
        """Get OPTIMADE data type from a Python type"""
        mapping = {
            "bool": cls.BOOLEAN,
            "int": cls.INTEGER,
            "float": cls.FLOAT,
            "complex": None,
            "generator": cls.LIST,
            "list": cls.LIST,
            "tuple": cls.LIST,
            "range": cls.LIST,
            "hash": cls.INTEGER,
            "str": cls.STRING,
            "bytes": cls.STRING,
            "bytearray": None,
            "memoryview": None,
            "set": cls.LIST,
            "frozenset": cls.LIST,
            "dict": cls.DICTIONARY,
            "dict_keys": cls.LIST,
            "dict_values": cls.LIST,
            "dict_items": cls.LIST,
            "NoneType": cls.UNKNOWN,
            "None": cls.UNKNOWN,
            "datetime": cls.TIMESTAMP,
            "date": cls.TIMESTAMP,
            "time": cls.TIMESTAMP,
            "datetime.datetime": cls.TIMESTAMP,
            "datetime.date": cls.TIMESTAMP,
            "datetime.time": cls.TIMESTAMP,
        }

        if isinstance(python_type, type):
            python_type = python_type.__name__
        elif isinstance(python_type, object):
            if str(python_type) in mapping:
                python_type = str(python_type)
            else:
                python_type = type(python_type).__name__

        return mapping.get(python_type, None)

    @classmethod
    def from_json_type(cls, json_type: str):
        """Get OPTIMADE data type from a named JSON type"""
        mapping = {
            "string": cls.STRING,
            "integer": cls.INTEGER,
            "number": cls.FLOAT,  # actually includes both integer and float
            "object": cls.DICTIONARY,
            "array": cls.LIST,
            "boolean": cls.BOOLEAN,
            "null": cls.UNKNOWN,
            # OpenAPI "format"s:
            "double": cls.FLOAT,
            "float": cls.FLOAT,
            "int32": cls.INTEGER,
            "int64": cls.INTEGER,
            "date": cls.TIMESTAMP,
            "date-time": cls.TIMESTAMP,
            "password": cls.STRING,
            "byte": cls.STRING,
            "binary": cls.STRING,
            # Non-OpenAPI "format"s, but may still be used by pydantic/FastAPI
            "email": cls.STRING,
            "uuid": cls.STRING,
            "uri": cls.STRING,
            "hostname": cls.STRING,
            "ipv4": cls.STRING,
            "ipv6": cls.STRING,
        }

        return mapping.get(json_type, None)


class AllowedJSONSchemaDataType(Enum):
    """The allowed values for `type` in the Property Definition restricted JSON Schema syntax."""

    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    NUMBER = "number"
    STRING = "string"
    INTEGER = "integer"
    
    @classmethod
    def from_optimade_type(cls, type: str) -> Optional["AllowedJSONSchemaDataType"]:
        """Returns a restricted JSON Schema type from an OPTIMADE type."""
        mapping = {
            DataType.STRING: cls.STRING,
            DataType.INTEGER: cls.INTEGER,
            DataType.FLOAT: cls.NUMBER,
            DataType.BOOLEAN: cls.BOOLEAN,
            DataType.TIMESTAMP: cls.STRING,
            DataType.LIST: cls.ARRAY,
            DataType.DICTIONARY: cls.OBJECT,
        }
        try:
            dt = DataType(type)
        except ValueError:
            return None

        return mapping.get(dt, None)




_PYDANTIC_FIELD_KWARGS = list(inspect.signature(Field).parameters.keys())

__all__ = (
    "CHEMICAL_SYMBOLS",
    "EXTRA_SYMBOLS",
    "ATOMIC_NUMBERS",
    "SemanticVersion",
    "SupportLevel",
)

OPTIMADE_SCHEMA_EXTENSION_KEYS = ["support", "queryable", "unit", "sortable"]
OPTIMADE_SCHEMA_EXTENSION_PREFIX = "x-optimade-"


class SupportLevel(Enum):
    """OPTIMADE property/field support levels"""

    MUST = "must"
    SHOULD = "should"
    OPTIONAL = "optional"


class QuerySupport(Enum):
    ALL_MANDATORY = "all mandatory"
    EQUALITY_ONLY = "equality only"
    PARTIAL = "partial"
    NONE = "none"


class StrictFieldInfo(FieldInfo):
    """Wraps the standard pydantic `FieldInfo` in order
    to prefix any custom keys from `StrictField`.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in OPTIMADE_SCHEMA_EXTENSION_KEYS:
            if key in self.extra:
                self.extra[f"{OPTIMADE_SCHEMA_EXTENSION_PREFIX}{key}"] = self.extra.pop(
                    key
                )


def StrictPydanticField(*args, **kwargs):
    """Wrapper for `Field` that uses `StrictFieldInfo` instead of
    the pydantic `FieldInfo`.
    """
    field_info = StrictFieldInfo(*args, **kwargs)
    field_info._validate()
    return field_info


def StrictField(
    *args: "Any",
    description: Optional[str] = None,
    **kwargs: "Any",
) -> StrictFieldInfo:
    """A wrapper around `pydantic.Field` that does the following:

    - Forbids any "extra" keys that would be passed to `pydantic.Field`,
      except those used elsewhere to modify the schema in-place,
      e.g. "uniqueItems", "pattern" and those added by OptimadeField, e.g.
      "unit", "queryable" and "sortable".
    - Emits a warning when no description is provided.

    Arguments:
        *args: Positional arguments passed through to `Field`.
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
            f"Not creating StrictField({args}, {kwargs}) with forbidden keywords {_banned}."
        )

    if description is not None:
        kwargs["description"] = description

    if description is None:
        warnings.warn(
            f"No description provided for StrictField specified by {args}, {kwargs}."
        )

    return StrictPydanticField(*args, **kwargs)


def OptimadeField(
    *args,
    support: Optional[SupportLevel] = None,
    queryable: Optional[SupportLevel] = None,
    unit: Optional[str] = None,
    **kwargs,
) -> Field:
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

    return StrictField(*args, **kwargs)


class SemanticVersion(str):
    """A custom type for a semantic version, using the recommended
    semver regexp from
    https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string.

    """

    regex = re.compile(
        r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            pattern=cls.regex.pattern,
            example=["0.10.1", "1.0.0-rc.2", "1.2.3-rc.5+develop"],
        )

    @classmethod
    def validate(cls, v: str):
        if not cls.regex.match(v):
            raise ValueError(
                f"Unable to validate the version string {v!r} as a semantic version (expected <major>.<minor>.<patch>)."
                "See https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string for more information."
            )

        return v

    @property
    def _match(self):
        """The result of the regex match."""
        return self.regex.match(self)

    @property
    def major(self) -> int:
        """The major version number."""
        return int(self._match.group(1))

    @property
    def minor(self) -> int:
        """The minor version number."""
        return int(self._match.group(2))

    @property
    def patch(self) -> int:
        """The patch version number."""
        return int(self._match.group(3))

    @property
    def prerelease(self) -> str:
        """The pre-release tag."""
        return self._match.group(4)

    @property
    def build_metadata(self) -> str:
        """The build metadata."""
        return self._match.group(5)

    @property
    def base_version(self) -> str:
        """The base version string without patch and metadata info."""
        return f"{self.major}.{self.minor}.{self.patch}"


def anonymous_element_generator():
    """Generator that yields the next symbol in the A, B, Aa, ... Az naming scheme."""
    from string import ascii_lowercase

    for size in itertools.count(1):
        for s in itertools.product(ascii_lowercase, repeat=size):
            s = list(s)
            s[0] = s[0].upper()
            yield "".join(s)


ANONYMOUS_ELEMENTS = tuple(itertools.islice(anonymous_element_generator(), 150))
""" Returns the first 150 values of the anonymous element generator. """

CHEMICAL_FORMULA_REGEXP = r"^([A-Z][a-z]?([2-9]|[1-9]\d+)?)+$"

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
