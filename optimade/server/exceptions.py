from abc import ABC
from fastapi import HTTPException as FastAPIHTTPException

__all__ = (
    "BadRequest",
    "VersionNotSupported",
    "Forbidden",
    "NotFound",
    "UnprocessableEntity",
    "NotImplementedResponse",
    "POSSIBLE_ERRORS",
)


class HTTPException(FastAPIHTTPException, ABC):
    """This abstract class makes it easier to subclass FastAPI's HTTPException with
    new status codes.

    It can also be useful when testing requires a string representation
    of an exception that contains the HTTPException
    detail string, rather than the standard Python exception message.

    Attributes:
        status_code: The HTTP status code accompanying this exception.
        title: A descriptive title for this exception.

    """

    status_code: int = None
    title: str

    def __init__(self, detail: str = None, headers: dict = None) -> None:
        if self.status_code is None:
            raise AttributeError(
                "HTTPException class {self.__class__.__name__} is missing required `status_code` attribute."
            )

        super().__init__(status_code=self.status_code, detail=detail, headers=headers)

    def __str__(self) -> str:
        return self.detail if self.detail is not None else self.__repr__()


class BadRequest(HTTPException):
    """400 Bad Request"""

    status_code: int = 400
    title: str = "Bad Request"


class VersionNotSupported(HTTPException):
    """553 Version Not Supported"""

    status_code: int = 553
    title: str = "Version Not Supported"


class Forbidden(HTTPException):
    """403 Forbidden"""

    status_code: int = 403
    title: str = "Forbidden"


class NotFound(HTTPException):
    """404 Not Found"""

    status_code: int = 404
    title: str = "Not Found"


class UnprocessableEntity(HTTPException):
    """422 Unprocessable Entity"""

    status_code: int = 422
    title: str = "Unprocessable Entity"


class InternalServerError(HTTPException):
    """500 Internal Server Error"""

    status_code: int = 500
    title: str = "Internal Server Error"


class NotImplementedResponse(HTTPException):
    """501 Not Implemented"""

    status_code: int = 501
    title: str = "Not Implemented"


POSSIBLE_ERRORS = (
    BadRequest,
    Forbidden,
    NotFound,
    UnprocessableEntity,
    InternalServerError,
    NotImplementedResponse,
    VersionNotSupported,
)
