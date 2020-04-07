import json
from pathlib import Path
from typing import List

import pytest

from optimade.adapters import Reference
from optimade.models import ReferenceResource


with open(Path(__file__).parent.joinpath("raw_test_references.json"), "r") as raw_data:
    RAW_REFERENCES: List[dict] = json.load(raw_data)


class TestReference:
    """Test Reference adapter"""

    def test_instantiate(self):
        """Try instantiating Reference for all raw test references"""
        for reference in RAW_REFERENCES:
            new_Reference = Reference(reference)
            assert isinstance(new_Reference.entry, ReferenceResource)

    def test_setting_entry(self, capfd):
        """Make sure entry can only be set once"""
        reference = Reference(RAW_REFERENCES[0])
        reference.entry = RAW_REFERENCES[1]
        captured = capfd.readouterr()
        assert "entry can only be set once and is already set." in captured.out

    @pytest.mark.skip(
        "Currently, there are no conversion types available for references"
    )
    def test_convert(self):
        """Test convert() works
        Choose currently known entry type - must be updated if no longer available.
        """
        reference = Reference(RAW_REFERENCES[0])

        if not reference._type_converters:
            pytest.fail("_type_converters is seemingly empty. This should not be.")

        chosen_type = "SOME_VALID_TYPE"
        if chosen_type not in reference._type_converters:
            pytest.fail(
                f"{chosen_type} not found in _type_converters: {reference._type_converters} - "
                "please update test tests/adapters/references/test_references.py:TestReference."
                "test_convert()"
            )

        converted_reference = reference.convert(chosen_type)
        assert isinstance(converted_reference, (str, None.__class__))
        assert converted_reference == reference._converted[chosen_type]

    def test_convert_wrong_format(self):
        """Test AttributeError is raised if format does not exist"""
        reference = Reference(RAW_REFERENCES[0])

        nonexistant_format = 0
        right_wrong_format_found = False
        while not right_wrong_format_found:
            if str(nonexistant_format) not in reference._type_converters:
                nonexistant_format = str(nonexistant_format)
                right_wrong_format_found = True
            else:
                nonexistant_format += 1

        with pytest.raises(AttributeError) as exc:
            reference.convert(nonexistant_format)
        assert f"Non-valid entry type to convert to: {nonexistant_format}." in str(exc)

    def test_getattr_order(self):
        """The order of getting an attribute should be:
        1. `get_<entry type format>`
        2. `<entry type attribute>`
        3. `raise AttributeError with custom message`
        """
        reference = Reference(RAW_REFERENCES[0])

        # If passing attribute starting with `get_`, it should call `self.convert()`
        with pytest.raises(AttributeError) as exc:
            reference.get_
        assert f"Non-valid entry type to convert to: " in str(exc)

        # If passing valid ReferenceResource attribute, it should return said attribute
        from optimade.models.references import Person

        assert isinstance(reference.attributes.authors[0], Person)

        # Otherwise, it should raise AttributeError
        for attribute in ("nonexistant_attribute", "attributes.nonexistant_attribute"):
            with pytest.raises(AttributeError) as exc:
                getattr(reference, attribute)
            assert f"Unknown attribute: {attribute}." in str(exc)
