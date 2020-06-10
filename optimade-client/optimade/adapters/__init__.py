# pylint: disable=undefined-variable
from .exceptions import *  # noqa: F403
from .references import *  # noqa: F403
from .structures import *  # noqa: F403
from pkg_resources import DistributionNotFound, get_distribution

__all__ = exceptions.__all__ + references.__all__ + structures.__all__  # noqa: F405

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass
