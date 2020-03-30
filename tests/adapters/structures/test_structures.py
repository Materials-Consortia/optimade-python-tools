import json
from pathlib import Path
from typing import List

import pytest
import unittest

from optimade.adapters import Structure
from optimade.models import StructureResource


class TestStructure(unittest.TestCase):
    """Test Structure adapter"""

    @pytest.fixture(autouse=True)
    def capfd(self, capfd):
        self.capfd = capfd

    @classmethod
    def setUpClass(cls):
        """Get raw test data"""
        with open(
            Path(__file__).parent.joinpath("raw_test_structures.json"), "r"
        ) as raw_data:
            cls.raw_structures: List[dict] = json.load(raw_data)

    def test_instantiate(self):
        """Try instantiating Structure for all raw test structures"""
        for structure in self.raw_structures:
            new_Structure = Structure(structure)
            self.assertIsInstance(new_Structure.entry, StructureResource)

    def test_setting_entry(self):
        """Make sure entry can only be set once"""
        structure = Structure(self.raw_structures[0])
        structure.entry = self.raw_structures[1]
        captured = self.capfd.readouterr()
        self.assertIn("entry can only be set once and is already set.", captured.out)

    def test_convert(self):
        """Test convert() works
        Choose currently known entry type - must be updated if no longer available.
        """
        try:
            from ase import Atoms
        except ImportError:
            Atoms = None

        structure = Structure(self.raw_structures[0])

        if not structure._type_converters:
            self.fail("_type_converters is seemingly empty. This should not be.")

        chosen_type = "ase"
        if chosen_type not in structure._type_converters:
            self.fail(
                f"{chosen_type} not found in _type_converters: {structure._type_converters} - "
                "please update test tests/adapters/structures/test_structures.py:TestStructure."
                "test_convert()"
            )

        converted_structure = structure.convert(chosen_type)
        self.assertIsInstance(converted_structure, Atoms.__class__)
        self.assertEqual(converted_structure, structure._converted[chosen_type])

    def test_convert_wrong_format(self):
        """Test AttributeError is raised if format does not exist"""
        structure = Structure(self.raw_structures[0])

        nonexistant_format = 0
        right_wrong_format_found = False
        while not right_wrong_format_found:
            if str(nonexistant_format) not in structure._type_converters:
                nonexistant_format = str(nonexistant_format)
                right_wrong_format_found = True
            else:
                nonexistant_format += 1

        with self.assertRaises(AttributeError) as exc:
            structure.convert(nonexistant_format)
        self.assertIn(
            f"Non-valid entry type to convert to: {nonexistant_format}.",
            str(exc.exception),
        )

    def test_getattr_order(self):
        """The order of getting an attribute should be:
        1. `get_<entry type format>`
        2. `<entry type attribute>`
        3. `raise AttributeError with custom message`
        """
        structure = Structure(self.raw_structures[0])

        # If passing attribute starting with `get_`, it should call `self.convert()`
        with self.assertRaises(AttributeError) as exc:
            structure.get_
        self.assertIn(f"Non-valid entry type to convert to: ", str(exc.exception))

        # If passing valid StructureResource attribute, it should return said attribute
        from optimade.models.structures import Species

        self.assertIsInstance(structure.attributes.species[0], Species)

        # Otherwise, it should raise AttributeError
        for attribute in ("nonexistant_attribute", "attributes.nonexistant_attribute"):
            with self.assertRaises(AttributeError) as exc:
                getattr(structure, attribute)
            self.assertIn(f"Unknown attribute: {attribute}.", str(exc.exception))
