from abc import ABC
from typing import Any, Dict, Optional, Tuple, Type

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


class OptimadeHTTPException(Exception, ABC):
    """This abstract class can be subclassed to define
    HTTP responses with the desired status codes, and
    detailed error strings to represent in the JSON:API
    error response.

    This class closely follows the `starlette.HTTPException` without
    requiring it as a dependency, so that such errors can also be
    raised from within client code.

    Attributes:
        status_code: The HTTP status code accompanying this exception.
        title: A descriptive title for this exception.
        detail: An optional string containing the details of the error.

    """

    status_code: int
    title: str
    detail: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None

    def __init__(
        self, detail: Optional[str] = None, headers: Optional[dict] = None
    ) -> None:
        if self.status_code is None:
            raise AttributeError(
                "HTTPException class {self.__class__.__name__} is missing required `status_code` attribute."
            )
        self.detail = detail
        self.headers = headers

    def __str__(self) -> str:
        return self.detail if self.detail is not None else self.__repr__()

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, detail={self.detail!r})"


class BadRequest(OptimadeHTTPException):
    """400 Bad Request"""

    status_code: int = 400
    title: str = "Bad Request"


class VersionNotSupported(OptimadeHTTPException):
    """553 Version Not Supported"""

    status_code: int = 553
    title: str = "Version Not Supported"


class Forbidden(OptimadeHTTPException):
    """403 Forbidden"""

    status_code: int = 403
    title: str = "Forbidden"


class NotFound(OptimadeHTTPException):
    """404 Not Found"""

    status_code: int = 404
    title: str = "Not Found"


class UnprocessableEntity(OptimadeHTTPException):
    """422 Unprocessable Entity"""

    status_code: int = 422
    title: str = "Unprocessable Entity"


class InternalServerError(OptimadeHTTPException):
    """500 Internal Server Error"""

    status_code: int = 500
    title: str = "Internal Server Error"


class NotImplementedResponse(OptimadeHTTPException):
    """501 Not Implemented"""

    status_code: int = 501
    title: str = "Not Implemented"


"""A tuple of the possible errors that can be returned by an OPTIMADE API."""
POSSIBLE_ERRORS: Tuple[Type[OptimadeHTTPException], ...] = (
    BadRequest,
    Forbidden,
    NotFound,
    UnprocessableEntity,
    InternalServerError,
    NotImplementedResponse,
    VersionNotSupported,
)
