from fastapi import Query
from pydantic import EmailStr  # pylint: disable=no-name-in-module

from optimade.models import NonnegativeInt

from .config import CONFIG


class EntryListingQueryParams:
    """Common query params for all Entry listing endpoints."""

    def __init__(
        self,
        *,
        filter: str = Query(  # pylint: disable=redefined-builtin
            "",
            description="""See [the full and latest OPTiMaDe spec](https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.rst) for filter query syntax.

Example: `chemical_formula = "Al" OR (prototype_formula = "AB" AND elements HAS Si, Al, O)`.
""",
        ),
        response_format: str = Query("json"),
        email_address: EmailStr = Query(""),
        response_fields: str = Query(""),
        sort: str = Query(""),
        page_limit: NonnegativeInt = Query(CONFIG.page_limit),
        page_offset: NonnegativeInt = Query(0),
        page_page: NonnegativeInt = Query(0),
        page_cursor: NonnegativeInt = Query(0),
        page_above: NonnegativeInt = Query(0),
        page_below: NonnegativeInt = Query(0),
    ):
        self.filter = filter
        self.response_format = response_format
        self.email_address = email_address
        self.response_fields = response_fields
        self.sort = sort
        self.page_limit = page_limit
        self.page_offset = page_offset
        self.page_page = page_page
        self.page_cursor = page_cursor
        self.page_above = page_above
        self.page_below = page_below


class SingleEntryQueryParams:
    """Common query params for single entry endpoints."""

    def __init__(
        self,
        *,
        response_format: str = Query("json"),
        email_address: EmailStr = Query(""),
        response_fields: str = Query(""),
    ):
        self.response_format = response_format
        self.email_address = email_address
        self.response_fields = response_fields
