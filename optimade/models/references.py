# pylint: disable=line-too-long,no-self-argument
from typing import List, Optional

from pydantic import AnyUrl, BaseModel, validator  # pylint: disable=no-name-in-module

from optimade.models.entries import EntryResource, EntryResourceAttributes
from optimade.models.utils import OptimadeField, SupportLevel

__all__ = ("Person", "ReferenceResourceAttributes", "ReferenceResource")


class Person(BaseModel):
    """A person, i.e., an author, editor or other."""

    name: str = OptimadeField(
        ...,
        description="""Full name of the person, REQUIRED.""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.OPTIONAL,
    )

    firstname: Optional[str] = OptimadeField(
        None,
        description="""First name of the person.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    lastname: Optional[str] = OptimadeField(
        None,
        description="""Last name of the person.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )


class ReferenceResourceAttributes(EntryResourceAttributes):
    """Model that stores the attributes of a reference.

    Many properties match the meaning described in the
    [BibTeX specification](http://bibtexml.sourceforge.net/btxdoc.pdf).

    """

    authors: Optional[List[Person]] = OptimadeField(
        None,
        description="List of person objects containing the authors of the reference.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    editors: Optional[List[Person]] = OptimadeField(
        None,
        description="List of person objects containing the editors of the reference.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    doi: Optional[str] = OptimadeField(
        None,
        description="The digital object identifier of the reference.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    url: Optional[AnyUrl] = OptimadeField(
        None,
        description="The URL of the reference.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    address: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    annote: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    booktitle: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    chapter: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    crossref: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    edition: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    howpublished: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    institution: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    journal: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    key: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    month: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    note: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    number: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    organization: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    pages: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    publisher: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    school: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    series: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    title: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    bib_type: Optional[str] = OptimadeField(
        None,
        description="Type of the reference, corresponding to the **type** property in the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    volume: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    year: Optional[str] = OptimadeField(
        None,
        description="Meaning of property matches the BiBTeX specification.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )


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

    type: str = OptimadeField(
        "references",
        description="""The name of the type of an entry.
- **Type**: string.
- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - **Response**: REQUIRED in the response.
    - MUST be an existing entry type.
    - The entry of type <type> and ID <id> MUST be returned in response to a request for `/<type>/<id>` under the versioned base URL.
- **Example**: `"structures"`""",
        regex="^references$",
        support=SupportLevel.MUST,
        queryable=SupportLevel.MUST,
    )
    attributes: ReferenceResourceAttributes

    @validator("attributes")
    def validate_attributes(cls, v):
        if not any(prop[1] is not None for prop in v):
            raise ValueError("reference object must have at least one field defined")
        return v
