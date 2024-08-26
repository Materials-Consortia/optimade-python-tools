from typing import Annotated, Optional, Union, get_args

from pydantic import Field

from optimade.models.utils import (
    ELEMENT_SYMBOLS_PATTERN,
    EXTENDED_CHEMICAL_SYMBOLS_PATTERN,
    SEMVER_PATTERN,
)

__all__ = ("ChemicalSymbol", "SemanticVersion")

ChemicalSymbol = Annotated[str, Field(pattern=EXTENDED_CHEMICAL_SYMBOLS_PATTERN)]

ElementSymbol = Annotated[str, Field(pattern=ELEMENT_SYMBOLS_PATTERN)]

SemanticVersion = Annotated[
    str,
    Field(
        pattern=SEMVER_PATTERN, examples=["0.10.1", "1.0.0-rc.2", "1.2.3-rc.5+develop"]
    ),
]

AnnotatedType = type(ChemicalSymbol)
OptionalType = type(Optional[str])
UnionType = type(Union[str, int])
NoneType = type(None)


def _get_origin_type(annotation: type) -> type:
    """Get the origin type of a type annotation.

    Parameters:
        annotation: The type annotation.

    Returns:
        The origin type.

    """
    # If the annotation is a Union, get the first non-None type (this includes
    # Optional[T])
    if isinstance(annotation, (OptionalType, UnionType)):
        for arg in get_args(annotation):
            if arg not in (None, NoneType):
                annotation = arg
                break

    # If the annotation is an Annotated type, get the first type
    if isinstance(annotation, AnnotatedType):
        annotation = get_args(annotation)[0]

    # Recursively unpack annotation, if it is a Union, Optional, or Annotated type
    while isinstance(annotation, (OptionalType, UnionType, AnnotatedType)):
        annotation = _get_origin_type(annotation)

    # Special case for Literal
    # NOTE: Expecting Literal arguments to all be of a single type
    arg = get_args(annotation)
    if arg and not isinstance(arg, type):
        # Expect arg to be a Literal type argument
        annotation = type(arg)

    # Ensure that the annotation is a builtin type
    return getattr(annotation, "__origin__", annotation)
