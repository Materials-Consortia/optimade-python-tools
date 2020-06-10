# pylint: disable=line-too-long,no-self-argument
from pydantic import Field, BaseModel, AnyUrl, validator
from typing import List, Optional

from .entries import EntryResource, EntryResourceAttributes


__all__ = ("Person", "ReferenceResourceAttributes", "ReferenceResource")


class Person(BaseModel):
    name: str = Field(..., decsription="""Full name of the person, REQUIRED.""")
    firstname: Optional[str] = Field(None, description="""First name of the person.""")
    lastname: Optional[str] = Field(None, description="""Last name of the person.""")


class ReferenceResourceAttributes(EntryResourceAttributes):
    """ Model that stores the attributes of a reference. Many properties match the
    meaning described in the
    [BibTeX specification](http://bibtexml.sourceforge.net/btxdoc.pdf).

    """

    authors: Optional[List[Person]] = Field(
        None,
        description="List of person objects containing the authors of the reference.",
    )
    editors: Optional[List[Person]] = Field(
        None,
        description="List of person objects containing the editors of the reference.",
    )

    doi: Optional[str] = Field(
        None, description="The digital object identifier of the reference."
    )

    url: Optional[AnyUrl] = Field(None, description="The URL of the reference.")

    address: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    annote: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    booktitle: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    chapter: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    crossref: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    edition: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    howpublished: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    institution: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    journal: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    key: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    month: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    note: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    number: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    organization: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    pages: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    publisher: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    school: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    series: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    title: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    bib_type: Optional[str] = Field(
        None,
        description="Type of the reference, corresponding to the **type** property in the BiBTeX specification.",
    )
    volume: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )
    year: Optional[str] = Field(
        None, description="Meaning of property matches the BiBTeX specification."
    )


class ReferenceResource(EntryResource):
    """ The :entry:`references` entries describe bibliographic references.
The following properties are used to provide the bibliographic details:

- **address**, **annote**, **booktitle**, **chapter**, **crossref**, **edition**, **howpublished**, **institution**, **journal**, **key**, **month**,
  **note**, **number**, **organization**, **pages**, **publisher**, **school**, **series**, **title**, **type**, **volume**, **year**:
  Meanings of these properties match the `BibTeX specification <http://bibtexml.sourceforge.net/btxdoc.pdf>`__, values are strings;

- **authors** and **editors**: lists of *person objects* which are dictionaries with the following keys:

  - **name**: Full name of the person, REQUIRED.
  - **firstname**, **lastname**: Parts of the person's name, OPTIONAL.

- **doi** and **url**: values are strings.

- **Requirements/Conventions**:

  - **Support**: OPTIONAL, i.e., any of the properties MAY be :val:`null`.
  - **Query**: Support for queries on any of these properties is OPTIONAL.
    If supported, filters MAY support only a subset of comparison operators.
  - Every references entry MUST contain at least one of the properties."""

    type: str = Field(
        default="references",
        const=True,
        description="""The name of the type of an entry. Any entry MUST be able to be fetched using the `base URL <Base URL_>`_ type and ID at the url :endpoint:`<base URL>/<type>/<id>`.
- **Type**: string.
- **Requirements/Conventions**:

  - **Support**: REQUIRED, MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property with support for all mandatory filter features.
  - **Response**: REQUIRED in the response.
  - MUST be an existing entry type.
  - The entry of type `<type>` and ID `<id>` MUST be returned in response to a request for :endpoint:`/<type>/<id>` under the versioned base URL.

- **Example**: :val:`"structures"`""",
    )
    attributes: ReferenceResourceAttributes

    @validator("attributes")
    def validate_attributes(cls, v):
        if not any(prop[1] is not None for prop in v):
            raise ValueError("reference object must have at least one field defined")
        return v
