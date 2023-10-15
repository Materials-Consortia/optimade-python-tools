import pytest
from pydantic import ValidationError

from optimade.models import Datatype, Provider


def test_convert_python_types():
    """Convert various Python types to OPTIMADE Data types"""
    from datetime import datetime

    expected_data_type = [
        Datatype.STRING,
        Datatype.INTEGER,
        Datatype.FLOAT,
        Datatype.LIST,
        Datatype.DICTIONARY,
        Datatype.UNKNOWN,
        Datatype.TIMESTAMP,
    ]

    python_types_as_strings = [
        "str",
        "int",
        "float",
        "list",
        "dict",
        "None",
        "datetime",
    ]
    python_types_as_types = [str, int, float, list, dict, None, datetime]

    test_none = None
    python_types_as_objects = [
        "Test",
        42,
        42.42,
        ["Test", 42],
        {"Test": 42},
        test_none,
        datetime.now(),
    ]

    for list_of_python_types in [
        python_types_as_strings,
        python_types_as_types,
        python_types_as_objects,
    ]:
        for index, python_type in enumerate(list_of_python_types):
            assert isinstance(
                Datatype.from_python_type(python_type), Datatype
            ), f"python_type: {python_type}"
            assert Datatype.from_python_type(python_type) == expected_data_type[index]


def test_convert_json_types():
    """Convert various JSON and OpenAPI types to OPTIMADE Data types"""
    json_types = [
        ("string", Datatype.STRING),
        ("integer", Datatype.INTEGER),
        ("number", Datatype.FLOAT),
        ("array", Datatype.LIST),
        ("object", Datatype.DICTIONARY),
        ("null", Datatype.UNKNOWN),
    ]
    openapi_formats = [
        ("date-time", Datatype.TIMESTAMP),
        ("email", Datatype.STRING),
        ("uri", Datatype.STRING),
    ]

    for list_of_schema_types in [json_types, openapi_formats]:
        for schema_type, optimade_type in list_of_schema_types:
            assert isinstance(
                Datatype.from_json_type(schema_type), Datatype
            ), f"json_type: {schema_type}"
            assert Datatype.from_json_type(schema_type) == optimade_type


def test_get_values():
    """Check all data values are returned sorted with get_values()"""
    sorted_data_types = [
        "boolean",
        "dictionary",
        "float",
        "integer",
        "list",
        "string",
        "timestamp",
        "unknown",
    ]
    assert Datatype.get_values() == sorted_data_types


@pytest.mark.parametrize(
    "prefix", ("exmpl", "exmpl_prefix", "exmpl123_prefix", "exmpl_")
)
def test_good_prefixes(prefix):
    """Check that some example provider objects can be deserialized."""

    provider = {
        "name": "Example",
        "description": "example",
        "homepage": None,
        "prefix": prefix,
    }

    assert Provider(**provider)


@pytest.mark.parametrize(
    "prefix",
    ("Example", "_exmpl", "123_exmpl", "", "example provider", "exampleProvider"),
)
def test_bad_prefixes(prefix):
    provider = {
        "name": "Example",
        "description": "example",
        "homepage": None,
        "prefix": prefix,
    }

    with pytest.raises(ValidationError):
        Provider(**provider)
