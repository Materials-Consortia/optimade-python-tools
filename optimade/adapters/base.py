import re
from typing import Union, Dict, Callable, Any, Tuple, List

from pydantic import BaseModel  # pylint: disable=no-name-in-module

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

    @staticmethod
    def _get_model_attributes(
        starting_instances: Union[Tuple[BaseModel], List[BaseModel]], name: str
    ) -> Any:
        """Helper method for retrieving the OPTIMADE model's attribute, supporting "."-nested attributes"""
        for res in starting_instances:
            nested_attributes = name.split(".")
            for nested_attribute in nested_attributes:
                if nested_attribute in getattr(res, "__fields__", {}):
                    res = getattr(res, nested_attribute)
                else:
                    res = None
                    break
            if res is not None:
                return res
        raise AttributeError

    def __getattr__(self, name: str) -> Any:
        """Get converted entry or attribute from OPTIMADE entry
        Support any level of "."-nested OPTIMADE ENTRY_RESOURCE attributes, e.g., `attributes.species` for StuctureResource.
        NOTE: All nested attributes must individually be subclasses of `pydantic.BaseModel`,
        i.e., one can not access nested attributes in lists by passing a "."-nested `name` to this method,
        e.g., `attributes.species.name` or `attributes.species[0].name` will not work for variable `name`.

        Order:
        - Try to return converted entry if using `as_<_type_converters key>`.
        - Try to return OPTIMADE ENTRY_RESOURCE (nested) attribute.
        - Try to return OPTIMADE ENTRY_RESOURCE.attributes (nested) attribute.
        - Raise AttributeError
        """
        # as_<entry_type>
        if name.startswith("as_"):
            entry_type = "_".join(name.split("_")[1:])
            return self.convert(entry_type)

        # Try returning ENTRY_RESOURCE attribute
        try:
            res = self._get_model_attributes((self.entry, self.entry.attributes), name)
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
            "If you want to get a converted entry as <entry_type> use `as_<entry_type>`, "
            f"where `<entry_type>` is one of {tuple(self._type_converters.keys()) + tuple(self._common_converters.keys())}\n"
            f"Otherwise, you can try to retrieve an OPTIMADE {entry_resource_name} attribute or property."
        )
