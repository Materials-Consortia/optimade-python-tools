import os
import sys

try:
    from optimade import __version__
except ImportError:
    raise ImportError(
        "optimade needs to be installed prior to running 'assert_version.py'"
    )

package_version = f"v{__version__}"

tag_version = os.getenv("TAG_VERSION")
tag_version = tag_version[len("refs/tags/") :]

if tag_version == package_version:
    print(f"The versions match: tag:'{tag_version}' == package:'{package_version}'")
    sys.exit(0)

print(
    f"""The current package version '{package_version}' does not equal the tag version '{tag_version}'.
Update package version by \"invoke setver --new-ver='{tag_version[1:]}'\" and re-commit.
Please remove the tag from both GitHub and your local repository and try again!"""
)
sys.exit(1)
