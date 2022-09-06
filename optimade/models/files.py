# pylint: disable=no-self-argument,line-too-long,no-name-in-module
"""This module documents the `files` entry type."""
from datetime import datetime
from typing import Optional, Dict, Literal

from optimade.models.entries import EntryResourceAttributes, EntryResource
from optimade.models.utils import (
    OptimadeField,
    StrictField,
    SupportLevel,
)


__all__ = (
    "FileResource",
    "FileResourceAttributes",
)


class FileResourceAttributes(EntryResourceAttributes):
    """This class contains the Field for the attributes used to represent a structure, e.g. unit cell, atoms, positions."""

    url: str = OptimadeField(
        ...,
        description="""The URL to get the contents of a file.

- **Type**: string
- **Requirements/Conventions**:

    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
    - **Response**: REQUIRED in the response.
    - The URL MUST point to the actual contents of a file (i.e. byte stream), not an intermediate (preview) representation.
      For example, if referring to a file on GitHub, a link should point to raw contents.

- **Examples**:

    - `"https://example.org/files/cifs/1000000.cif"`
""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.OPTIONAL,
    )

    url_stable_until: Optional[datetime] = OptimadeField(
        ...,
        description="""Point in time until which the URL in `url` is guaranteed to stay stable.
- **Type**: timestamp
- **Requirements/Conventions**:

  - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
  - **Query**: Support for queries on this property is OPTIONAL.
  - `null` means that there is no stability guarantee for the URL in `url`.
    Indefinite support could be communicated by providing a date sufficiently far in the future, for example, `9999-12-31`.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    name: str = OptimadeField(
        ...,
        description="""Base name of a file.
- **Type**: string
- **Requirements/Conventions**:

  - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
  - **Query**: Support for queries on this property is OPTIONAL.
  - File name extension is an integral part of a file name and, if available, MUST be included.

- **Examples**:

  - `"1000000.cif"`""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.OPTIONAL,
    )

    size: Optional[int] = OptimadeField(
        ...,
        description="""Size of a file in bytes.
- **Type**: integer
- **Requirements/Conventions**:

  - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
  - **Query**: Support for queries on this property is OPTIONAL.
  - If provided, it MUST be guaranteed that either exact size of a file is given or its upper bound.
    This way if a client reserves a static buffer or truncates the download stream after this many bytes the whole file would be received.
    Such provision is included to allow the providers to serve on-the-fly compressed files.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    media_type: Optional[str] = OptimadeField(
        ...,
        description="""Media type identifier for a file as per `RFC 6838 Media Type Specifications and Registration Procedures <https://datatracker.ietf.org/doc/html/rfc6838>`__.
- **Type**: string
- **Requirements/Conventions**:

  - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
  - **Query**: Support for queries on this property is OPTIONAL.

- **Examples**:

  - `"chemical/x-cif"`""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    version: Optional[str] = OptimadeField(
        ...,
        description="""Version information of a file (e.g. commit, revision, timestamp).
- **Type**: string
- **Requirements/Conventions**:

  - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
  - **Query**: Support for queries on this property is OPTIONAL.
  - If provided, it MUST be guaranteed that file contents pertaining to the same combination of `id` and `version` are the same.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    modification_timestamp: Optional[datetime] = OptimadeField(
        ...,
        description="""Timestamp of the last modification of file contents.
  A modification is understood as an addition, change or deletion of one or more bytes, resulting in file contents different from the previous.
- **Type**: timestamp
- **Requirements/Conventions**:

  - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
  - **Query**: Support for queries on this property is OPTIONAL.
  - Timestamps of subsequent file modifications SHOULD be increasing (not earlier than previous timestamps).""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    description: Optional[str] = OptimadeField(
        ...,
        description="""Free-form description of a file.
- **Type**: string
- **Requirements/Conventions**:

  - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
  - **Query**: Support for queries on this property is OPTIONAL.

- **Examples**:

  - `"POSCAR format file"`""",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.OPTIONAL,
    )

    checksums: Optional[
        Dict[Literal["md5", "sha1", "sha224", "sha384", "sha512"], str]
    ] = OptimadeField(
        ...,
        description="""Dictionary providing checksums of file contents.
* **Type**: dictionary with keys identifying checksum functions and values (strings) giving the actual checksums
* **Requirements/Conventions**:

  - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
  - **Query**: Support for queries on this property is OPTIONAL.
  - Supported dictionary keys: `md5`, `sha1`, `sha224`, `sha256`, `sha384`, `sha512`.
    Checksums outside this list MAY be used, but their names MUST be prefixed by database-provider-specific namespace prefix (see appendix `Database-Provider-Specific Namespace Prefixes`_).""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    atime: Optional[datetime] = OptimadeField(
        ...,
        description="""Time of last access of a file as per POSIX standard.
- **Type**: timestamp
- **Requirements/Conventions**:

- **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
- **Query**: Support for queries on this property is OPTIONAL.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    ctime: Optional[datetime] = OptimadeField(
        ...,
        description="""Time of last status change of a file as per POSIX standard.
- **Type**: timestamp
- **Requirements/Conventions**:

  - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
  - **Query**: Support for queries on this property is OPTIONAL.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    mtime: Optional[datetime] = OptimadeField(
        ...,
        description="""Time of last modification of a file as per POSIX standard.
- **Type**: timestamp
- **Requirements/Conventions**:

  - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
  - **Query**: Support for queries on this property is OPTIONAL.
  - It should be noted that the values of `last_modified`, `modification_timestamp` and `mtime` do not necessary match.
    `last_modified` pertains to the modification of the OPTIMADE metadata, `modification_timestamp` pertains to file contents and `mtime` pertains to the modification of the file (not necessary changing its contents).
    For example, appending an empty string to a file would result in the change of `mtime` in some operating systems, but this would not be deemed as a modification of its contents.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )


class FileResource(EntryResource):
    """Representing a file."""

    type: str = StrictField(
        "files",
        description="""The name of the type of an entry.

- **Type**: string.

- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - **Response**: REQUIRED in the response.
    - MUST be an existing entry type.
    - The entry of type `<type>` and ID `<id>` MUST be returned in response to a request for `/<type>/<id>` under the versioned base URL.

- **Examples**:
    - `"files"`""",
        regex="^files$",
        support=SupportLevel.MUST,
        queryable=SupportLevel.MUST,
    )

    attributes: FileResourceAttributes
