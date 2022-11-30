"""Reproduced imports from `optimade.exceptions` for backwards-compatibility."""

from optimade.exceptions import (
    POSSIBLE_ERRORS,
    BadRequest,
    Forbidden,
    InternalServerError,
    NotFound,
    NotImplementedResponse,
    OptimadeHTTPException,
    UnprocessableEntity,
    VersionNotSupported,
)

__all__ = (
    "OptimadeHTTPException",
    "BadRequest",
    "VersionNotSupported",
    "Forbidden",
    "NotFound",
    "UnprocessableEntity",
    "InternalServerError",
    "NotImplementedResponse",
    "POSSIBLE_ERRORS",
)
