import re
from typing import Union, Dict, Callable, Any

from optimade.models import EntryResource


class EntryAdapter:
    """Base class for lazy resource entry adapters
    :param entry: JSON OPTIMADE single resource entry.
    """

    ENTRY_RESOURCE: EntryResource = EntryResource
    _type_converters: Dict[str, Callable] = {}

    def __init__(self, entry: dict):
        self._entry = None
        self._converted = {}

        self.entry = entry

        # Note that these return also the default values for otherwise non-provided properties.
        self._common_converters = {
            "json": self.entry.json,  # Return JSON serialized string, see https://pydantic-docs.helpmanual.io/usage/exporting_models/#modeljson
            "dict": self.entry.dict,  # Return Python dict, see https://pydantic-docs.helpmanual.io/usage/exporting_models/#modeldict
        }

    @property
    def entry(self):
        """Get OPTIMADE entry"""
        return self._entry

    @entry.setter
    def entry(self, value: dict):
        """Set OPTIMADE entry
        If already set, print that this can _only_ be set once.
        """
        if self._entry is None:
            self._entry = self.ENTRY_RESOURCE(**value)
        else:
            print("entry can only be set once and is already set.")

    def convert(self, format: str) -> Any:
        """Convert OPTIMADE entry to desired format"""
        if (
            format not in self._type_converters
            and format not in self._common_converters
        ):
            raise AttributeError(
                f"Non-valid entry type to convert to: {format}\n"
                f"Valid entry types: {tuple(self._type_converters.keys()) + tuple(self._common_converters.keys())}"
            )

        if self._converted.get(format, None) is None:
            if format in self._type_converters:
                self._converted[format] = self._type_converters[format](self.entry)
            else:
                self._converted[format] = self._common_converters[format]()

        return self._converted[format]

    def __getattr__(self, name: str) -> Any:
        """Get converted entry or attribute from OPTIMADE entry
        Order:
        - Try to return converted entry if using `get_<_type_converters value>`.
        - Try to return OPTIMADE ENTRY_RESOURCE attribute.
        - Try to return OPTIMADE ENTRY_RESOURCE.attributes attribute.
        - Raise AttributeError
        """
        # get_<entry_type>
        if name.startswith("get_"):
            entry_type = "_".join(name.split("_")[1:])
            return self.convert(entry_type)

        # Try returning:
        # 1. ENTRY_RESOURCE attribute
        # 2. ENTRY_RESOURCE.attributes attribute (an ENTRY_RESOURCE property)
        try:
            res = getattr(self.entry, name)
        except AttributeError:
            # Try to see if we are dealing with a nested attribute name, e.g., attributes.species
            if "." in name:
                res = None
                nested_attributes = name.split(".")
                try:
                    for nested_attribute in nested_attributes:
                        res = self.__getattr__(nested_attribute)
                except AttributeError:
                    pass
                else:
                    return res
        else:
            return res

        try:
            res = getattr(self.entry.attributes, name)
        except AttributeError:
            pass
        else:
            return res

        # Non-valid attribute
        entry_resource_name = re.match(
            r"(<class ')([a-zA-Z_]+\.)*([a-zA-Z_]+)('>)", str(self.ENTRY_RESOURCE)
        )
        entry_resource_name = (
            entry_resource_name.group(3)
            if entry_resource_name is not None
            else "UNKNOWN RESOURCE"
        )
        raise AttributeError(
            f"Unknown attribute: {name}\n"
            "If you want to get a converted entry use `get_<entry_type>`, "
            f"where `<entry_type>` is one of {tuple(self._type_converters.keys()) + tuple(self._common_converters.keys())}\n"
            f"Otherwise, you can try to retrieve an OPTIMADE {entry_resource_name} attribute or property."
        )
