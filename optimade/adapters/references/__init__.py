from typing import Union

from optimade.models import ReferenceResource

from optimade.adapters.base import EntryAdapter


__all__ = ("Reference",)


class Reference(EntryAdapter):
    """Lazy structure converter
    :param structure: JSON OPTIMADE single structures resource entry.
    """

    ENTRY_RESOURCE = ReferenceResource
    _type_converters = {}
