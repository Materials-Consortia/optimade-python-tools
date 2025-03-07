"""Test Structure adapter"""

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from optimade.adapters.structures import Structure

try:
    import aiida  # noqa: F401
    import ase  # noqa: F401
    import jarvis  # noqa: F401
    import numpy  # noqa: F401
    import pymatgen  # noqa: F401
except ImportError:
    all_modules_found = False
else:
    all_modules_found = True

if TYPE_CHECKING:
    from typing import Any, Union


def test_instantiate(RAW_STRUCTURES: "list[dict[str, Any]]") -> None:
    """Try instantiating Structure for all raw test structures"""
    from optimade.adapters.structures import Structure
    from optimade.models.structures import StructureResource

    for structure in RAW_STRUCTURES:
        new_Structure = Structure(structure)
        assert isinstance(new_Structure.entry, StructureResource)


def test_setting_entry(RAW_STRUCTURES: "list[dict[str, Any]]") -> None:
    """Make sure entry can only be set once"""
    from optimade.adapters.structures import Structure

    structure = Structure(RAW_STRUCTURES[0])
    with pytest.raises(AttributeError):
        structure.entry = RAW_STRUCTURES[1]


def test_convert(structure: "Structure") -> None:
    """Test convert() works
    Choose currently known entry type - must be updated if no longer available.
    """
    pytest.importorskip("numpy")
    if not structure._type_converters:
        pytest.fail("_type_converters is seemingly empty. This should not be.")

    chosen_type = "cif"
    if chosen_type not in structure._type_converters:
        pytest.fail(
            f"{chosen_type} not found in _type_converters: {structure._type_converters} - "
            "please update test tests/adapters/structures/test_structures.py:TestStructure."
            "test_convert()"
        )

    converted_structure = structure.convert(chosen_type)
    assert isinstance(converted_structure, (str, None.__class__))
    assert converted_structure == structure._converted[chosen_type]


def test_convert_wrong_format(structure: "Structure") -> None:
    """Test AttributeError is raised if format does not exist"""
    nonexistant_format: "Union[int, str]" = 0
    right_wrong_format_found = False
    while not right_wrong_format_found:
        if str(nonexistant_format) not in structure._type_converters:
            nonexistant_format = str(nonexistant_format)
            right_wrong_format_found = True
        else:
            assert isinstance(nonexistant_format, int)
            nonexistant_format += 1

    with pytest.raises(
        AttributeError,
        match=f"Non-valid entry type to convert to: {nonexistant_format}",
    ):
        structure.convert(nonexistant_format)


def test_getattr_order(structure: "Structure") -> None:
    """The order of getting an attribute should be:
    1. `as_<entry type format>`
    2. `<entry type attribute>`
    3. `<entry type attributes attributes>`
    4. `raise AttributeError` with custom message
    """
    # If passing attribute starting with `as_`, it should call `self.convert()`
    with pytest.raises(AttributeError, match="Non-valid entry type to convert to: "):
        structure.as_

    # If passing valid StructureResource attribute, it should return said attribute
    # Test also nested attributes with `getattr()`.
    for attribute, attribute_type in (
        ("id", str),
        ("species", list),
        ("attributes.species", list),
    ):
        assert isinstance(getattr(structure, attribute), attribute_type)

    # Otherwise, it should raise AttributeError
    for attribute in ("nonexistant_attribute", "attributes.nonexistant_attribute"):
        with pytest.raises(AttributeError, match=f"Unknown attribute: {attribute}"):
            getattr(structure, attribute)


@pytest.mark.skipif(
    all_modules_found,
    reason="This test checks what happens if a conversion-dependent module cannot be found. "
    "All could be found, i.e., it has no meaning.",
)
def test_no_module_conversion(structure: "Structure") -> None:
    """Make sure a warnings is raised and None is returned for conversions with non-existing modules"""
    import importlib

    from optimade.adapters.warnings import AdapterPackageNotFound

    CONVERSION_MAPPING = {
        "aiida": ["aiida_structuredata"],
        "ase": ["ase"],
        "numpy": ["cif", "pdb", "pdbx_mmcif"],
        "pymatgen": ["pymatgen"],
        "jarvis": ["jarvis"],
    }

    modules_to_test = []
    for module in ("aiida", "ase", "numpy", "pymatgen", "jarvis"):
        try:
            importlib.import_module(module)
        except (ImportError, ModuleNotFoundError):
            modules_to_test.append(module)

    if not modules_to_test:
        pytest.fail("No modules found to test - it seems all modules are installed.")

    for module in modules_to_test:
        for conversion_function in CONVERSION_MAPPING[module]:
            with pytest.warns(
                AdapterPackageNotFound, match="not found, cannot convert structure to"
            ):
                converted_structure = structure.convert(conversion_function)
            assert converted_structure is None


def test_common_converters(
    raw_structure: "dict[str, Any]", RAW_STRUCTURES: "list[dict[str, Any]]"
) -> None:
    """Test common converters"""
    from optimade.adapters.structures import Structure
    from optimade.models.structures import StructureResource

    structure = Structure(raw_structure)

    assert structure.as_json == StructureResource(**raw_structure).model_dump_json()
    assert structure.as_dict == StructureResource(**raw_structure).model_dump()

    # Since calling .model_dump() and .model_dump_json() will return also all
    # default-valued properties, the raw structure should at least be a sub-set of the
    # resource's full list of properties.
    for raw_structure in RAW_STRUCTURES:
        raw_structure_property_set = set(raw_structure.keys())
        resource_property_set = set(Structure(raw_structure).as_dict.keys())
        assert raw_structure_property_set.issubset(resource_property_set)


def compare_lossy_conversion(
    structure_attributes: "dict[str, Any]",
    reconverted_structure_attributes: "dict[str, Any]",
) -> None:
    """Compare two structures, allowing for some loss of information and mapping of prefixed keys."""

    try:
        import numpy as np
    except ImportError:
        pytest.node.warn(
            pytest.PytestWarning(
                "numpy not found, some cases of conversion tests will be skipped"
            )
        )
        np = None

    lossy_keys = (
        "chemical_formula_descriptive",
        "chemical_formula_hill",
        "last_modified",
        "assemblies",
        "attached",
        "immutable_id",
        "species",
        "fractional_site_positions",
        "space_group_symmetry_operations_xyz",
        "space_group_symbol_hall",
        "space_group_symbol_hermann_mauguin",
        "space_group_symbol_hermann_mauguin_extended",
        "space_group_it_number",
    )
    array_keys = ("cartesian_site_positions", "lattice_vectors")

    for k in reconverted_structure_attributes:
        if k not in lossy_keys:
            if k in array_keys and np is not None:
                np.testing.assert_almost_equal(
                    reconverted_structure_attributes[k], structure_attributes[k]
                )
            elif k.startswith("_"):
                # ugly way of checking if a substring exists in the initial structure
                for i in range(len(k)):
                    subkey = k[i:]
                    if subkey in structure_attributes:
                        assert (
                            reconverted_structure_attributes[k]
                            == structure_attributes[subkey]
                        )
                        break
                else:
                    raise ValueError(f"No subkey of {k} was found in initial structure")

            else:
                assert reconverted_structure_attributes[k] == structure_attributes[k]


def _get_formats() -> "list[str]":
    """Get all available formats"""
    from optimade.adapters.structures import Structure

    return [
        k for k in Structure._type_ingesters.keys() if k in Structure._type_converters
    ]


@pytest.mark.parametrize(
    "format",
    _get_formats(),
)
def test_two_way_conversion(
    RAW_STRUCTURES: "list[dict[str, Any]]", format: str
) -> None:
    """Test two-way conversion"""
    from optimade.adapters.structures import Structure

    for structure in RAW_STRUCTURES:
        new_structure = Structure(structure)
        converted_structure = new_structure.convert(format)
        if converted_structure is None:
            continue
        reconverted_structure = Structure.ingest_from(
            converted_structure, format
        ).entry.model_dump()
        compare_lossy_conversion(
            structure["attributes"], reconverted_structure["attributes"]
        )


@pytest.mark.parametrize(
    "format",
    _get_formats(),
)
def test_two_way_conversion_with_implicit_type(
    RAW_STRUCTURES: "list[dict[str, Any]]", format: str
) -> None:
    """Test two-way conversion with implicit type"""
    from optimade.adapters.structures import Structure

    for structure in RAW_STRUCTURES:
        new_structure = Structure(structure)
        converted_structure = new_structure.convert(format)
        if converted_structure is None:
            continue
        reconverted_structure = Structure.ingest_from(
            converted_structure, format=None
        ).entry.model_dump()

        compare_lossy_conversion(
            structure["attributes"], reconverted_structure["attributes"]
        )


def test_load_good_structure_from_url(RAW_STRUCTURES, mock_requests_get):
    for raw_structure in RAW_STRUCTURES:
        mock_requests_get({"data": raw_structure})
        structure = Structure.from_url("https://example.com/v1/structures/1")
        assert structure


def test_load_bad_structure_from_url(raw_structure, mock_requests_get):
    mock_requests_get({}, status_code=400)
    with pytest.raises(RuntimeError):
        Structure.from_url("https://example.com/v1/structures/1")

    mock_requests_get({"data": raw_structure}, status_code=400)
    with pytest.raises(RuntimeError):
        Structure.from_url("https://example.com/v1/structures/1")

    mock_requests_get(["bad_json_data"])
    with pytest.raises(RuntimeError):
        Structure.from_url("https://example.com/v1/structures/1")

    mock_requests_get({"data": [raw_structure, raw_structure]})
    with pytest.raises(RuntimeError):
        Structure.from_url("https://example.com/v1/structures/1")

    raw_structure["id"] = None
    mock_requests_get({"data": raw_structure})
    with pytest.raises(ValidationError):
        Structure.from_url("https://example.com/v1/structures/1")
