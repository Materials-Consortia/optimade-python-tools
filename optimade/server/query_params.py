from fastapi import Query
from pydantic import EmailStr  # pylint: disable=no-name-in-module

from .config import CONFIG


class EntryListingQueryParams:
    """
    Common query params for all Entry listing endpoints.

    Attributes:
        filter (str): A filter string, in the format described in section API Filtering Format Specification of the specification.

        response_format (str): The output format requested (see section Response Format).
            Defaults to the format string 'json', which specifies the standard output format described in this specification.

            **Example**: `http://example.com/v1/structures?response_format=xml`

        email_address (EmailStr): An email address of the user making the request.
            The email SHOULD be that of a person and not an automatic system.

            **Example**: `http://example.com/v1/structures?email_address=user@example.com`

        response_fields (str): A comma-delimited set of fields to be provided in the output.
            If provided, these fields MUST be returned along with the REQUIRED fields.
            Other OPTIONAL fields MUST NOT be returned when this parameter is present.

            **Example**: `http://example.com/v1/structures?response_fields=last_modified,nsites`

        sort (str): If supporting sortable queries, an implementation MUST use the `sort` query parameter with format as specified
            by [JSON API 1.0](https://jsonapi.org/format/1.0/#fetching-sorting).

            An implementation MAY support multiple sort fields for a single query.
            If it does, it again MUST conform to the JSON API 1.0 specification.

            If an implementation supports sorting for an entry listing endpoint, then the `/info/<entries>` endpoint MUST include,
            for each field name `<fieldname>` in its `data.properties.<fieldname>` response value that can be used for sorting,
            the key `sortable` with value `true`.
            If a field name under an entry listing endpoint supporting sorting cannot be used for sorting, the server MUST either
            leave out the `sortable` key or set it equal to `false` for the specific field name.
            The set of field names, with `sortable` equal to `true` are allowed to be used in the "sort fields" list according to
            its definition in the JSON API 1.0 specification.
            The field `sortable` is in addition to each property description and other OPTIONAL fields.
            An example is shown in the section Entry Listing Info Endpoints.

        page_limit (int): Sets a numerical limit on the number of entries returned.
            See [JSON API 1.0](https://jsonapi.org/format/1.0/#fetching-pagination).
            The API implementation MUST return no more than the number specified.
            It MAY return fewer. The database MAY have a maximum limit and not accept larger numbers
            (in which case an error code -- `403 Forbidden` -- MUST be returned).
            The default limit value is up to the API implementation to decide.

            **Example**: `http://example.com/optimade/v1/structures?page_limit=100`

        page_offset (int): RECOMMENDED for use with _offset-based_ pagination: using `page_offset` and `page_limit` is RECOMMENDED.

            **Example**: Skip 50 structures and fetch up to 100: `/structures?page_offset=50&page_limit=100`.

        page_number (int): RECOMMENDED for use with _page-based_ pagination: using `page_number` and `page_limit` is RECOMMENDED.
            It is RECOMMENDED that the first page has number 1, i.e., that `page_number` is 1-based.

            **Example**: Fetch page 2 of up to 50 structures per page: `/structures?page_number=2&page_limit=50`.

        page_cursor (int): RECOMMENDED for use with _cursor-based_ pagination: using `page_cursor` and `page_limit` is RECOMMENDED.

        page_above (int): RECOMMENDED for use with _value-based_ pagination: using `page_above`/`page_below` and `page_limit` is RECOMMENDED.

            **Example**: Fetch up to 100 structures above sort-field value 4000 (in this example, server chooses to fetch results sorted by
            increasing `id`, so `page_above` value refers to an `id` value): `/structures?page_above=4000&page_limit=100`.

        page_below (int): RECOMMENDED for use with _value-based_ pagination: using `page_above`/`page_below` and `page_limit` is RECOMMENDED.

        include (str): A server MAY implement the JSON API concept of returning [compound documents](https://jsonapi.org/format/1.0/#document-compound-documents)
            by utilizing the `include` query parameter as specified by [JSON API 1.0](https://jsonapi.org/format/1.0/#fetching-includes).

            All related resource objects MUST be returned as part of an array value for the top-level `included` field,
            see the section JSON Response Schema: Common Fields.

            The value of `include` MUST be a comma-separated list of "relationship paths", as defined in the [JSON API](https://jsonapi.org/format/1.0/#fetching-includes).
            If relationship paths are not supported, or a server is unable to identify a relationship path a `400 Bad Request` response MUST be made.

            The **default value** for `include` is `references`. This means `references` entries MUST always be included under the top-level field
            `included` as default, since a server assumes if `include` is not specified by a client in the request, it is still specified as `include=references`.
            Note, if a client explicitly specifies `include` and leaves out `references`, `references` resource objects MUST NOT be included under the top-level
            field `included`, as per the definition of `included`, see section JSON Response Schema: Common Fields.

            **Note**: A query with the parameter `include` set to the empty string means no related resource objects are to be returned under the top-level field `included`.

        api_hint (str): If the client provides the parameter, the value SHOULD have the format `vMAJOR` or `vMAJOR.MINOR`,
            where MAJOR is a major version and MINOR is a minor version of the API.
            For example, if a client appends `api_hint=v1.0` to the query string, the hint provided is for major version 1 and minor version 0.

    """

    def __init__(
        self,
        *,
        filter: str = Query(  # pylint: disable=redefined-builtin
            "",
            description="A filter string, in the format described in section API Filtering Format Specification of the specification.",
        ),
        response_format: str = Query(
            "json",
            description="The output format requested (see section Response Format).\nDefaults to the format string 'json', which specifies the standard output format described in this specification.\nExample: `http://example.com/v1/structures?response_format=xml`",
        ),
        email_address: EmailStr = Query(
            "",
            description="An email address of the user making the request.\nThe email SHOULD be that of a person and not an automatic system.\nExample: `http://example.com/v1/structures?email_address=user@example.com`",
        ),
        response_fields: str = Query(
            "",
            description="A comma-delimited set of fields to be provided in the output.\nIf provided, these fields MUST be returned along with the REQUIRED fields.\nOther OPTIONAL fields MUST NOT be returned when this parameter is present.\nExample: `http://example.com/v1/structures?response_fields=last_modified,nsites`",
            regex=r"([a-z_][a-z_0-9]*(,[a-z_][a-z_0-9]*)*)?",
        ),
        sort: str = Query(
            "",
            description='If supporting sortable queries, an implementation MUST use the `sort` query parameter with format as specified by [JSON API 1.0](https://jsonapi.org/format/1.0/#fetching-sorting).\n\nAn implementation MAY support multiple sort fields for a single query.\nIf it does, it again MUST conform to the JSON API 1.0 specification.\n\nIf an implementation supports sorting for an entry listing endpoint, then the `/info/<entries>` endpoint MUST include, for each field name `<fieldname>` in its `data.properties.<fieldname>` response value that can be used for sorting, the key `sortable` with value `true`.\nIf a field name under an entry listing endpoint supporting sorting cannot be used for sorting, the server MUST either leave out the `sortable` key or set it equal to `false` for the specific field name.\nThe set of field names, with `sortable` equal to `true` are allowed to be used in the "sort fields" list according to its definition in the JSON API 1.0 specification.\nThe field `sortable` is in addition to each property description and other OPTIONAL fields.\nAn example is shown in the section Entry Listing Info Endpoints.',
            regex=r"([a-z_][a-z_0-9]*(,[a-z_][a-z_0-9]*)*)?",
        ),
        page_limit: int = Query(
            CONFIG.page_limit,
            description="Sets a numerical limit on the number of entries returned.\nSee [JSON API 1.0](https://jsonapi.org/format/1.0/#fetching-pagination).\nThe API implementation MUST return no more than the number specified.\nIt MAY return fewer.\nThe database MAY have a maximum limit and not accept larger numbers (in which case an error code -- 403 Forbidden -- MUST be returned).\nThe default limit value is up to the API implementation to decide.\nExample: `http://example.com/optimade/v1/structures?page_limit=100`",
            ge=0,
        ),
        page_offset: int = Query(
            0,
            description="RECOMMENDED for use with _offset-based_ pagination: using `page_offset` and `page_limit` is RECOMMENDED.\nExample: Skip 50 structures and fetch up to 100: `/structures?page_offset=50&page_limit=100`.",
            ge=0,
        ),
        page_number: int = Query(
            0,
            description="RECOMMENDED for use with _page-based_ pagination: using `page_number` and `page_limit` is RECOMMENDED.\nIt is RECOMMENDED that the first page has number 1, i.e., that `page_number` is 1-based.\nExample: Fetch page 2 of up to 50 structures per page: `/structures?page_number=2&page_limit=50`.",
            ge=0,
        ),
        page_cursor: int = Query(
            0,
            description="RECOMMENDED for use with _cursor-based_ pagination: using `page_cursor` and `page_limit` is RECOMMENDED.",
            ge=0,
        ),
        page_above: int = Query(
            0,
            description="RECOMMENDED for use with _value-based_ pagination: using `page_above`/`page_below` and `page_limit` is RECOMMENDED.\nExample: Fetch up to 100 structures above sort-field value 4000 (in this example, server chooses to fetch results sorted by increasing `id`, so `page_above` value refers to an `id` value): `/structures?page_above=4000&page_limit=100`.",
            ge=0,
        ),
        page_below: int = Query(
            0,
            description="RECOMMENDED for use with _value-based_ pagination: using `page_above`/`page_below` and `page_limit` is RECOMMENDED.",
            ge=0,
        ),
        include: str = Query(
            "references",
            description='A server MAY implement the JSON API concept of returning [compound documents](https://jsonapi.org/format/1.0/#document-compound-documents) by utilizing the `include` query parameter as specified by [JSON API 1.0](https://jsonapi.org/format/1.0/#fetching-includes).\n\nAll related resource objects MUST be returned as part of an array value for the top-level `included` field, see the section JSON Response Schema: Common Fields.\n\nThe value of `include` MUST be a comma-separated list of "relationship paths", as defined in the [JSON API](https://jsonapi.org/format/1.0/#fetching-includes).\nIf relationship paths are not supported, or a server is unable to identify a relationship path a `400 Bad Request` response MUST be made.\n\nThe **default value** for `include` is `references`.\nThis means `references` entries MUST always be included under the top-level field `included` as default, since a server assumes if `include` is not specified by a client in the request, it is still specified as `include=references`.\nNote, if a client explicitly specifies `include` and leaves out `references`, `references` resource objects MUST NOT be included under the top-level field `included`, as per the definition of `included`, see section JSON Response Schema: Common Fields.\n\n> **Note**: A query with the parameter `include` set to the empty string means no related resource objects are to be returned under the top-level field `included`.',
        ),
        api_hint: str = Query(
            "",
            description="If the client provides the parameter, the value SHOULD have the format `vMAJOR` or `vMAJOR.MINOR`, where MAJOR is a major version and MINOR is a minor version of the API. For example, if a client appends `api_hint=v1.0` to the query string, the hint provided is for major version 1 and minor version 0.",
            regex=r"(v[0-9]+(\.[0-9]+)?)?",
        ),
    ):
        self.filter = filter
        self.response_format = response_format
        self.email_address = email_address
        self.response_fields = response_fields
        self.sort = sort
        self.page_limit = page_limit
        self.page_offset = page_offset
        self.page_number = page_number
        self.page_cursor = page_cursor
        self.page_above = page_above
        self.page_below = page_below
        self.include = include


class SingleEntryQueryParams:
    """
    Common query params for single entry endpoints.

    Attributes:
        response_format (str): The output format requested (see section Response Format).
            Defaults to the format string 'json', which specifies the standard output format described in this specification.

            **Example**: `http://example.com/v1/structures?response_format=xml`

        email_address (EmailStr): An email address of the user making the request.
            The email SHOULD be that of a person and not an automatic system.

            **Example**: `http://example.com/v1/structures?email_address=user@example.com`

        response_fields (str): A comma-delimited set of fields to be provided in the output.
            If provided, these fields MUST be returned along with the REQUIRED fields.
            Other OPTIONAL fields MUST NOT be returned when this parameter is present.

            **Example**: `http://example.com/v1/structures?response_fields=last_modified,nsites`

        include (str): A server MAY implement the JSON API concept of returning [compound documents](https://jsonapi.org/format/1.0/#document-compound-documents)
            by utilizing the `include` query parameter as specified by [JSON API 1.0](https://jsonapi.org/format/1.0/#fetching-includes).

            All related resource objects MUST be returned as part of an array value for the top-level `included` field,
            see the section JSON Response Schema: Common Fields.

            The value of `include` MUST be a comma-separated list of "relationship paths", as defined in the [JSON API](https://jsonapi.org/format/1.0/#fetching-includes).
            If relationship paths are not supported, or a server is unable to identify a relationship path a `400 Bad Request` response MUST be made.

            The **default value** for `include` is `references`. This means `references` entries MUST always be included under the top-level field
            `included` as default, since a server assumes if `include` is not specified by a client in the request, it is still specified as `include=references`.
            Note, if a client explicitly specifies `include` and leaves out `references`, `references` resource objects MUST NOT be included under the top-level
            field `included`, as per the definition of `included`, see section JSON Response Schema: Common Fields.

            **Note**: A query with the parameter `include` set to the empty string means no related resource objects are to be returned under the top-level field `included`.

        api_hint (str): If the client provides the parameter, the value SHOULD have the format `vMAJOR` or `vMAJOR.MINOR`,
            where MAJOR is a major version and MINOR is a minor version of the API.
            For example, if a client appends `api_hint=v1.0` to the query string, the hint provided is for major version 1 and minor version 0.

    """

    def __init__(
        self,
        *,
        response_format: str = Query(
            "json",
            description="The output format requested (see section Response Format).\nDefaults to the format string 'json', which specifies the standard output format described in this specification.\nExample: `http://example.com/v1/structures?response_format=xml`",
        ),
        email_address: EmailStr = Query(
            "",
            description="An email address of the user making the request.\nThe email SHOULD be that of a person and not an automatic system.\nExample: `http://example.com/v1/structures?email_address=user@example.com`",
        ),
        response_fields: str = Query(
            "",
            description="A comma-delimited set of fields to be provided in the output.\nIf provided, these fields MUST be returned along with the REQUIRED fields.\nOther OPTIONAL fields MUST NOT be returned when this parameter is present.\nExample: `http://example.com/v1/structures?response_fields=last_modified,nsites`",
            regex=r"([a-z_][a-z_0-9]*(,[a-z_][a-z_0-9]*)*)?",
        ),
        include: str = Query(
            "references",
            description='A server MAY implement the JSON API concept of returning [compound documents](https://jsonapi.org/format/1.0/#document-compound-documents) by utilizing the `include` query parameter as specified by [JSON API 1.0](https://jsonapi.org/format/1.0/#fetching-includes).\n\nAll related resource objects MUST be returned as part of an array value for the top-level `included` field, see the section JSON Response Schema: Common Fields.\n\nThe value of `include` MUST be a comma-separated list of "relationship paths", as defined in the [JSON API](https://jsonapi.org/format/1.0/#fetching-includes).\nIf relationship paths are not supported, or a server is unable to identify a relationship path a `400 Bad Request` response MUST be made.\n\nThe **default value** for `include` is `references`.\nThis means `references` entries MUST always be included under the top-level field `included` as default, since a server assumes if `include` is not specified by a client in the request, it is still specified as `include=references`.\nNote, if a client explicitly specifies `include` and leaves out `references`, `references` resource objects MUST NOT be included under the top-level field `included`, as per the definition of `included`, see section JSON Response Schema: Common Fields.\n\n> **Note**: A query with the parameter `include` set to the empty string means no related resource objects are to be returned under the top-level field `included`.',
        ),
        api_hint: str = Query(
            "",
            description="If the client provides the parameter, the value SHOULD have the format `vMAJOR` or `vMAJOR.MINOR`, where MAJOR is a major version and MINOR is a minor version of the API. For example, if a client appends `api_hint=v1.0` to the query string, the hint provided is for major version 1 and minor version 0.",
            regex=r"(v[0-9]+(\.[0-9]+)?)?",
        ),
    ):
        self.response_format = response_format
        self.email_address = email_address
        self.response_fields = response_fields
        self.include = include
