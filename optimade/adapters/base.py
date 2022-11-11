"""
The base for all adapters.

An entry resource adapter is a tool to wrap OPTIMADE JSON-deserialized Python dictionaries
in the relevant pydantic model for the particular resource.

This means data resources in an OPTIMADE REST API response can be converted to valid Python
types written specifically for them.
One can then use the standard pydantic functionality on the wrapped objects, reasoning about
the embedded hierarchical types as well as retrieve default values for properties not supplied
by the raw API response resource.

Furthermore, the entry resource adapter allows conversion between the entry resource and any
implemented equivalent data structure.

See [`Reference`][optimade.adapters.references.adapter.Reference] and
[`Structure`][optimade.adapters.structures.adapter.Structure] to find out what the entry
resources can be converted to for [`ReferenceResource`][optimade.models.references.ReferenceResource]s
and [`StructureResource`][optimade.models.structures.StructureResource]s, respectively.
"""
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from optimade.adapters.logger import LOGGER
from optimade.models.entries import EntryResource


class EntryAdapter:
    """
    Base class for lazy resource entry adapters.

    Attributes:
        ENTRY_RESOURCE: Entry resource to store entry as.
        _type_converters: Dictionary of valid conversion types for entry.
        as_<_type_converters>: Convert entry to a type listed in `_type_converters`.
        from_<_type_converters>: Convert an external type to the corresponding OPTIMADE model.

    """

    ENTRY_RESOURCE: Type[EntryResource] = EntryResource
    _type_converters: Dict[str, Callable] = {}
    _type_ingesters: Dict[str, Callable] = {}

    def __init__(self, entry: dict) -> None:
        """
        Parameters:
            entry (dict): A JSON OPTIMADE single resource entry.
        """
        self._entry: Optional[EntryResource] = None
        self._converted: Dict[str, Any] = {}

        self.entry: EntryResource = entry  # type: ignore[assignment]

        # Note that these return also the default values for otherwise non-provided properties.
        self._common_converters = {
            # Return JSON serialized string, see https://pydantic-docs.helpmanual.io/usage/exporting_models/#modeljson
            "json": self.entry.json,  # type: ignore[attr-defined]
            # Return Python dict, see https://pydantic-docs.helpmanual.io/usage/exporting_models/#modeldict
            "dict": self.entry.dict,  # type: ignore[attr-defined]
        }

    @property
    def entry(self) -> EntryResource:
        """Get OPTIMADE entry.

        Returns:
            The entry resource.

        """
        return self._entry  # type: ignore[return-value]

    @entry.setter
    def entry(self, value: dict) -> None:
        """Set OPTIMADE entry.

        If already set, print that this can _only_ be set once.

        Parameters:
            value (dict): Raw entry to wrap in the relevant pydantic model represented by `ENTRY_RESOURCE`.

        """
        if self._entry is None:
            self._entry = self.ENTRY_RESOURCE(**value)
        else:
            LOGGER.warning("entry can only be set once and is already set.")

    def convert(self, format: str) -> Any:
        """Convert OPTIMADE entry to desired format.

        Parameters:
            format (str): Type or format to which the entry should be converted.

        Raises:
            AttributeError: If `format` can not be found in `_type_converters` or `_common_converters`.

        Returns:
            The converted entry according to the desired format or type.

        """
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
        starting_instances: Union[Tuple[BaseModel, ...], List[BaseModel]], name: str
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
        """Get converted entry or attribute from OPTIMADE entry.

        Support any level of "."-nested OPTIMADE `ENTRY_RESOURCE` attributes, e.g.,
        `attributes.species` for [`StuctureResource`][optimade.models.structures.StructureResource].

        Note:
            All nested attributes must individually be subclasses of `pydantic.BaseModel`,
            i.e., one can not access nested attributes in lists by passing a "."-nested `name` to this method,
            e.g., `attributes.species.name` or `attributes.species[0].name` will not work for variable `name`.

        Order:

        - Try to return converted entry if using `as_<_type_converters key>`.
        - Try to return OPTIMADE `ENTRY_RESOURCE` (nested) attribute.
        - Try to return OPTIMADE `ENTRY_RESOURCE.attributes` (nested) attribute.
        - Raise `AttributeError`.

        Parameters:
            name (str): Requested attribute.

        Raises:
            AttributeError: If the requested attribute is not recognized.
                See above for the description of the order in which an attribute is tested for validity.

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
        _entry_resource_name = re.match(
            r"(<class ')([a-zA-Z_]+\.)*([a-zA-Z_]+)('>)", str(self.ENTRY_RESOURCE)
        )
        entry_resource_name = (
            _entry_resource_name.group(3)
            if _entry_resource_name is not None
            else "UNKNOWN RESOURCE"
        )
        raise AttributeError(
            f"Unknown attribute: {name}\n"
            "If you want to get a converted entry as <entry_type> use `as_<entry_type>`, "
            f"where `<entry_type>` is one of {tuple(self._type_converters.keys()) + tuple(self._common_converters.keys())}\n"
            f"Otherwise, you can try to retrieve an OPTIMADE {entry_resource_name} attribute or property."
        )
