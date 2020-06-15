""" This submodule loads the filter examples that have been scraped
from the specification.

- Both `filters.txt` and `optional_filters.txt.` are automatically
generated files containing all examples from the specification. It
is generated using the `invoke` task `parse_spec_for_filters`.

When being loaded in, these filter examples are also made more concrete
by replacing references to vague `values`/`value` with specific examples.

"""

from pathlib import Path

__all__ = ["MANDATORY_FILTER_EXAMPLES", "OPTIONAL_FILTER_EXAMPLES"]

ALIASES = {"values": '"1", "2", "3"', "value": "1", "inverse": "1"}


def _load_filters_and_apply_aliases(path):
    """ Load a text file containing example filters with one
    filter per line, and apply aliases to swap out dummy values
    with more concrete examples.

    Parameters:
        path (str/Path): the filename to load.

    Returns:
        list: a list of filters.

    """
    with open(path, "r") as f:
        _filters = []
        for line in f.readlines():
            for alias in ALIASES:
                if alias in line:
                    line = line.replace(alias, ALIASES[alias])
            _filters.append(line)

    return _filters


OPTIONAL_FILTER_EXAMPLES = _load_filters_and_apply_aliases(
    Path(__file__).parent.joinpath("optional_filters.txt").resolve()
)
MANDATORY_FILTER_EXAMPLES = _load_filters_and_apply_aliases(
    Path(__file__).parent.joinpath("filters.txt").resolve()
)
