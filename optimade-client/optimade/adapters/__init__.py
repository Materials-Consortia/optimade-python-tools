# pylint: disable=undefined-variable
from .exceptions import *
from .references import *
from .structures import *


__all__ = exceptions.__all__ + references.__all__ + structures.__all__
from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass
