from typing import Annotated

from pydantic import Field

from optimade.models.utils import EXTENDED_CHEMICAL_SYMBOLS_PATTERN, SEMVER_PATTERN

__all__ = ("ChemicalSymbol", "SemanticVersion")

ChemicalSymbol = Annotated[str, Field(pattern=EXTENDED_CHEMICAL_SYMBOLS_PATTERN)]

SemanticVersion = Annotated[
    str,
    Field(
        pattern=SEMVER_PATTERN, example=["0.10.1", "1.0.0-rc.2", "1.2.3-rc.5+develop"]
    ),
]
