class OptimadeWarning(Warning):
    """Base Warning for the `optimade` package"""

    def __init__(self, detail: str = None, title: str = None, *args) -> None:
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
