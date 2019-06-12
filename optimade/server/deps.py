from configparser import ConfigParser
from pathlib import Path

from fastapi import Query
from pydantic import EmailStr

from .models.util import NonnegativeInt

config = ConfigParser()
config.read(Path(__file__).resolve().parent.joinpath('config.ini'))
RESPONSE_LIMIT = config['DEFAULT'].getint('RESPONSE_LIMIT')


filter_description = """\
See [the full OPTiMaDe spec](https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md) for filter
query syntax.

Example: `chemical_formula = "Al" OR (prototype_formula = "AB" AND elements HAS Si, Al, O)`.
"""


class EntryListingQueryParams:
    """
    Common query params for all Entry listing endpoints.

    response_limit is a duplicate of page[limit]. The former is a MUST by optimade, whereas the latter is a SHOULD
    by JSON API. If response_limit is given, it takes precedence over any page[limit] value.

    """

    def __init__(
            self,
            *,
            filter: str = Query(None, description=filter_description),
            response_format: str = "jsonapi",
            email_address: EmailStr = None,
            response_limit: NonnegativeInt = RESPONSE_LIMIT,
            response_fields: str = None,
            sort: str = None,
            page_offset: NonnegativeInt = Query(0, alias="page[offset]"),
            page_limit: NonnegativeInt = Query(RESPONSE_LIMIT, alias="page[limit]"),
    ):
        self.filter = filter
        self.response_format = response_format
        self.email_address = email_address
        self.response_limit = response_limit
        self.response_fields = response_fields
        self.sort = sort
        self.page_offset = page_offset
        self.page_limit = page_limit
