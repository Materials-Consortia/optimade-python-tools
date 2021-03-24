__version__ = "0.13.3"
__api_version__ = "1.0.1"


import sys


class OptimadeDeprecationWarning(Warning):
    """Special deprecation warning"""


if sys.version_info.minor == 6:
    # Python 3.6
    import warnings

    warnings.warn(
        "v0.14 of the `optimade` package will be the last to support Python 3.6. "
        "Please upgrade to Python 3.7+ to use v0.15 and later versions of `optimade`.",
        OptimadeDeprecationWarning,
    )
