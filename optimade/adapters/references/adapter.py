from optimade.models import ReferenceResource
from optimade.adapters.base import EntryAdapter


class Reference(EntryAdapter):
    """Lazy reference resource converter
    :param reference: a single JSON OPTIMADE reference resource entry.
    """

    ENTRY_RESOURCE = ReferenceResource
