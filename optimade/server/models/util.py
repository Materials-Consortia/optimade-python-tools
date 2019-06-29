from typing import cast, Any, Dict, Type

from pydantic import ConstrainedInt, errors
from pydantic.types import OptionalInt
from pydantic.validators import list_validator


class NonnegativeInt(ConstrainedInt):
    ge = 0