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
