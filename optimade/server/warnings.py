"""This submodule maintains backwards compatibility with the old `optimade.server.warnings` module,
which previously implemented the imported warnings directly.

"""

from optimade.warnings import (
    FieldValueNotRecognized,
    MissingExpectedField,
    OptimadeWarning,
    QueryParamNotUsed,
    TimestampNotRFCCompliant,
    TooManyValues,
    UnknownProviderProperty,
    UnknownProviderQueryParameter,
)

__all__ = (
    "FieldValueNotRecognized",
    "MissingExpectedField",
    "OptimadeWarning",
    "QueryParamNotUsed",
    "TimestampNotRFCCompliant",
    "TooManyValues",
    "UnknownProviderProperty",
    "UnknownProviderQueryParameter",
)
