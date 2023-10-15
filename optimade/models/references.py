from typing import Annotated, Any, Literal, Optional

from pydantic import AnyUrl, BaseModel, field_validator

from optimade.models.entries import EntryResource, EntryResourceAttributes
from optimade.models.utils import OptimadeField, SupportLevel

__all__ = ("Person", "ReferenceResourceAttributes", "ReferenceResource")


class Person(BaseModel):
    """A person, i.e., an author, editor or other."""

    name: Annotated[
        str,
        OptimadeField(
            description="""Full name of the person, REQUIRED.""",
            support=SupportLevel.MUST,
            queryable=SupportLevel.OPTIONAL,
        ),
    ]

    firstname: Annotated[
        Optional[str],
        OptimadeField(
            description="""First name of the person.""",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    lastname: Annotated[
        Optional[str],
        OptimadeField(
            description="""Last name of the person.""",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None


class ReferenceResourceAttributes(EntryResourceAttributes):
    """Model that stores the attributes of a reference.

    Many properties match the meaning described in the
    [BibTeX specification](http://bibtexml.sourceforge.net/btxdoc.pdf).

    """

    authors: Annotated[
        Optional[list[Person]],
        OptimadeField(
            description="List of person objects containing the authors of the reference.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    editors: Annotated[
        Optional[list[Person]],
        OptimadeField(
            description="List of person objects containing the editors of the reference.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    doi: Annotated[
        Optional[str],
        OptimadeField(
            description="The digital object identifier of the reference.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    url: Annotated[
        Optional[AnyUrl],
        OptimadeField(
            description="The URL of the reference.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    address: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    annote: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    booktitle: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    chapter: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    crossref: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    edition: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    howpublished: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    institution: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    journal: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    key: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    month: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    note: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    number: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    organization: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    pages: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    publisher: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    school: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    series: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    title: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    bib_type: Annotated[
        Optional[str],
        OptimadeField(
            description="Type of the reference, corresponding to the **type** property in the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    volume: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None

    year: Annotated[
        Optional[str],
        OptimadeField(
            description="Meaning of property matches the BiBTeX specification.",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
        ),
    ] = None


class ReferenceResource(EntryResource):
    """The `references` entries describe bibliographic references.

    The following properties are used to provide the bibliographic details:

    - **address**, **annote**, **booktitle**, **chapter**, **crossref**, **edition**, **howpublished**, **institution**, **journal**, **key**, **month**, **note**, **number**, **organization**, **pages**, **publisher**, **school**, **series**, **title**, **volume**, **year**: meanings of these properties match the [BibTeX specification](http://bibtexml.sourceforge.net/btxdoc.pdf), values are strings;
    - **bib_type**: type of the reference, corresponding to **type** property in the BibTeX specification, value is string;
    - **authors** and **editors**: lists of *person objects* which are dictionaries with the following keys:
        - **name**: Full name of the person, REQUIRED.
        - **firstname**, **lastname**: Parts of the person's name, OPTIONAL.
    - **doi** and **url**: values are strings.
    - **Requirements/Conventions**:
        - **Support**: OPTIONAL support in implementations, i.e., any of the properties MAY be `null`.
        - **Query**: Support for queries on any of these properties is OPTIONAL.
            If supported, filters MAY support only a subset of comparison operators.
        - Every references entry MUST contain at least one of the properties.

    """

    type: Annotated[
        Literal["references"],
        OptimadeField(
            description="""The name of the type of an entry.
- **Type**: string.
- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - **Response**: REQUIRED in the response.
    - MUST be an existing entry type.
    - The entry of type <type> and ID <id> MUST be returned in response to a request for `/<type>/<id>` under the versioned base URL.
- **Example**: `"structures"`""",
            pattern="^references$",
            support=SupportLevel.MUST,
            queryable=SupportLevel.MUST,
        ),
    ] = "references"
    attributes: ReferenceResourceAttributes

    @field_validator("attributes", mode="before")
    @classmethod
    def validate_attributes(cls, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            if isinstance(value, BaseModel):
                value = value.model_dump()
            else:
                raise TypeError("attributes field must be a mapping")
        if not any(prop[1] is not None for prop in value):
            raise ValueError("reference object must have at least one field defined")
        return value
