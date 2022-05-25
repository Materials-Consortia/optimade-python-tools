__version__ = "0.17.2"
__api_version__ = "1.1.0"

import sys

if sys.version_info.minor == 7:
    import warnings

    warnings.filterwarnings(
        action="once",
        message=r"v0\.17 of the `optimade` package.*",
        category=DeprecationWarning,
        append=False,
    )
    warnings.warn(
        "v0.17 of the `optimade` package will be the last to support Python 3.7. "
        "Please upgrade to Python 3.8+ to use v0.18 and later versions of `optimade`.",
        DeprecationWarning,
    )
