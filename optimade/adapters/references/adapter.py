from typing import Type

from optimade.adapters.base import EntryAdapter
from optimade.models import ReferenceResource


class Reference(EntryAdapter):
    """
    Lazy reference resource converter.

    Go to [`EntryAdapter`][optimade.adapters.base.EntryAdapter] to see the full list of methods
    and properties.

    Attributes:
        ENTRY_RESOURCE (ReferenceResource): This adapter stores entry resources as
            [`ReferenceResource`][optimade.models.references.ReferenceResource]s.
        _type_converters (Dict[str, Callable]): Dictionary of valid conversion types for entry.

            There are currently no available types.
        as_<_type_converters>: Convert entry to a type listed in `_type_converters`.

    """

    ENTRY_RESOURCE: Type[ReferenceResource] = ReferenceResource
