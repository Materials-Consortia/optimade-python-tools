import json
from pathlib import Path
from typing import List

import pytest

from optimade.adapters import Structure
from optimade.models import StructureResource


with open(Path(__file__).parent.joinpath("raw_test_structures.json"), "r") as raw_data:
    RAW_STRUCTURES: List[dict] = json.load(raw_data)


class TestStructure:
    """Test Structure adapter"""

    def test_instantiate(self):
        """Try instantiating Structure for all raw test structures"""
        for structure in RAW_STRUCTURES:
            new_Structure = Structure(structure)
            assert isinstance(new_Structure.entry, StructureResource)

    def test_setting_entry(self, capfd):
        """Make sure entry can only be set once"""
        structure = Structure(RAW_STRUCTURES[0])
        structure.entry = RAW_STRUCTURES[1]
        captured = capfd.readouterr()
        assert "entry can only be set once and is already set." in captured.out

    def test_convert(self):
        """Test convert() works
        Choose currently known entry type - must be updated if no longer available.
        """
        try:
            from ase import Atoms
        except ImportError:
            Atoms = None

        structure = Structure(RAW_STRUCTURES[0])

        if not structure._type_converters:
            pytest.fail("_type_converters is seemingly empty. This should not be.")

        chosen_type = "ase"
        if chosen_type not in structure._type_converters:
            pytest.fail(
                f"{chosen_type} not found in _type_converters: {structure._type_converters} - "
                "please update test tests/adapters/structures/test_structures.py:TestStructure."
                "test_convert()"
            )

        converted_structure = structure.convert(chosen_type)
        assert isinstance(converted_structure, (None.__class__, Atoms))
        assert converted_structure == structure._converted[chosen_type]

    def test_convert_wrong_format(self):
        """Test AttributeError is raised if format does not exist"""
        structure = Structure(RAW_STRUCTURES[0])

        nonexistant_format = 0
        right_wrong_format_found = False
        while not right_wrong_format_found:
            if str(nonexistant_format) not in structure._type_converters:
                nonexistant_format = str(nonexistant_format)
                right_wrong_format_found = True
            else:
                nonexistant_format += 1

        with pytest.raises(AttributeError) as exc:
            structure.convert(nonexistant_format)
        assert f"Non-valid entry type to convert to: {nonexistant_format}." in str(exc)

    def test_getattr_order(self):
        """The order of getting an attribute should be:
        1. `get_<entry type format>`
        2. `<entry type attribute>`
        3. `raise AttributeError with custom message`
        """
        structure = Structure(RAW_STRUCTURES[0])

        # If passing attribute starting with `get_`, it should call `self.convert()`
        with pytest.raises(AttributeError) as exc:
            structure.get_
        assert f"Non-valid entry type to convert to: " in str(exc)

        # If passing valid StructureResource attribute, it should return said attribute
        from optimade.models.structures import Species

        assert isinstance(structure.attributes.species[0], Species)

        # Otherwise, it should raise AttributeError
        for attribute in ("nonexistant_attribute", "attributes.nonexistant_attribute"):
            with pytest.raises(AttributeError) as exc:
                getattr(structure, attribute)
            assert f"Unknown attribute: {attribute}." in str(exc)
