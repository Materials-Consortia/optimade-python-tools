from fastapi import HTTPException


class BadRequest(HTTPException):
    """400 Bad Request"""

    def __init__(
        self,
        status_code: int = 400,
        detail: str = None,
        headers: dict = None,
        title: str = "Bad Request",
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.title = title


class VersionNotSupported(HTTPException):
    """553 Version Not Supported"""

    def __init__(
        self,
        status_code: int = 553,
        detail: str = None,
        headers: dict = None,
        title: str = "Version Not Supported",
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.title = title


class Forbidden(HTTPException):
    """403 Forbidden"""

    def __init__(
        self,
        status_code: int = 403,
        detail: str = None,
        headers: dict = None,
        title: str = "Forbidden",
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.title = title
