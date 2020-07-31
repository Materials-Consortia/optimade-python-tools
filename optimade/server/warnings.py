class OptimadeWarning(Warning):
    """Base Warning for the `optimade` package"""

    def __init__(self, detail: str = None, title: str = None, *args) -> None:
        detail = detail if detail else self.__doc__
        super().__init__(detail, *args)
        self.detail = detail
        self.title = title if title else self.__class__.__name__

    def __repr__(self) -> str:
        attrs = {
            "detail": self.detail,
            "title": self.title,
        }
        return "<{:s}({:s})>".format(
            self.__class__.__name__,
            " ".join(
                [
                    f"{attr}={value!r}"
                    for attr, value in attrs.items()
                    if value is not None
                ]
            ),
        )

    def __str__(self) -> str:
        return self.detail if self.detail is not None else ""


class FieldNotCreated(OptimadeWarning):
    """A non-essential field could not be created"""


class UnmatchedValues(OptimadeWarning):
    """Values of the same field or resource differ, where they should be equal"""


class FieldNotRecognized(OptimadeWarning):
    """A field used in the request is not recognised by this implementation."""


class LogsNotSaved(OptimadeWarning):
    """Log files are not saved.

    This is usually due to not being able to a specified log folder or write to files
    in the specified log location, i.e., a `PermissionError` has been raised.

    To solve this, either set the `OPTIMADE_LOG_DIR` environment variable to a location
    you have permission to write to or create the `/var/log/optimade` folder, which is
    the default logging folder, with write permissions for the Unix user running the server.
    """
