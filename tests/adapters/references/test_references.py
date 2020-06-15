import pytest

from optimade.adapters import Reference
from optimade.models import ReferenceResource


class TestReference:
    """Test Reference adapter"""

    def test_instantiate(self, RAW_REFERENCES):
        """Try instantiating Reference for all raw test references"""
        for reference in RAW_REFERENCES:
            new_Reference = Reference(reference)
            assert isinstance(new_Reference.entry, ReferenceResource)

    def test_setting_entry(self, capfd, RAW_REFERENCES):
        """Make sure entry can only be set once"""
        reference = Reference(RAW_REFERENCES[0])
        reference.entry = RAW_REFERENCES[1]
        captured = capfd.readouterr()
        assert "entry can only be set once and is already set." in captured.out

    @pytest.mark.skip(
        "Currently, there are no conversion types available for references"
    )
    def test_convert(self, reference):
        """Test convert() works
        Choose currently known entry type - must be updated if no longer available.
        """
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

    def test_convert_wrong_format(self, reference):
        """Test AttributeError is raised if format does not exist"""
        nonexistant_format = 0
        right_wrong_format_found = False
        while not right_wrong_format_found:
            if str(nonexistant_format) not in reference._type_converters:
                nonexistant_format = str(nonexistant_format)
                right_wrong_format_found = True
            else:
                nonexistant_format += 1

        with pytest.raises(
            AttributeError,
            match=f"Non-valid entry type to convert to: {nonexistant_format}",
        ):
            reference.convert(nonexistant_format)

    def test_getattr_order(self, reference):
        """The order of getting an attribute should be:
        1. `as_<entry type format>`
        2. `<entry type attribute>`
        3. `<entry type attributes attributes>`
        3. `raise AttributeError with custom message`
        """
        # If passing attribute starting with `as_`, it should call `self.convert()`
        with pytest.raises(
            AttributeError, match="Non-valid entry type to convert to: "
        ):
            reference.as_

        # If passing valid ReferenceResource attribute, it should return said attribute
        for attribute, attribute_type in (
            ("id", str),
            ("authors", list),
            ("attributes.authors", list),
        ):
            assert isinstance(getattr(reference, attribute), attribute_type)

        # Otherwise, it should raise AttributeError
        for attribute in ("nonexistant_attribute", "attributes.nonexistant_attribute"):
            with pytest.raises(AttributeError, match=f"Unknown attribute: {attribute}"):
                getattr(reference, attribute)
