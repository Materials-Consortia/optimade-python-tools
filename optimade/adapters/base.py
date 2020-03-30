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
        self._converted = dict.fromkeys(self._type_converters)

        self.entry = entry

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
        if format not in self._type_converters:
            raise AttributeError(
                f"Non-valid entry type to convert to: {format}. "
                f"Valid entry types: {tuple(self._type_converters.keys())}"
            )

        if self._converted[format] is None:
            self._converted[format] = self._type_converters[format](self.entry)

        return self._converted[format]

    def __getattr__(self, name: str) -> Any:
        """Get converted entry or attribute from OPTIMADE entry
        Order:
        - Try to return converted entry if using `get_<_type_converters value>`.
        - Try to return OPTIMADE ENTRY_RESOURCE attribute.
        - Raise AttributeError
        """
        # get_<entry_type>
        if name.startswith("get_"):
            entry_type = "_".join(name.split("_")[1:])
            return self.convert(entry_type)

        # Try returning ENTRY_RESOURCE attribute
        try:
            res = getattr(self.entry, name)
        except AttributeError:
            pass
        else:
            return res

        # Non-valid attribute
        raise AttributeError(
            f"Unknown attribute: {name}.\n"
            "If you want to get a converted entry use `get_<entry_type>`, "
            f"where `<entry_type>` is one of {tuple(self._type_converters.keys())}\n"
            "Otherwise, you can try to retrieve an OPTIMADE "
            f"{self.ENTRY_RESOURCE.__class__.__name__} attribute."
        )
