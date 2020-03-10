""" This submodule loads the filter examples that have been scraped
from the specification.

- `filters.txt` is a automatically generated file containing all
examples. It is generated using the `invoke` task `parse_spec_for_filters`.
- `optional_filters.txt` is human-generated, and allows for filters that
are inside `filters.txt` to be skipped, if it has been deemed that they
are optional (external to the parsed file). In the future, it is hoped
that the spec will be fully parseable and as such this file could be
generated automatically too.

When being loaded in, these filter examples are also made more concrete
by replacing references to vague `values`/`value` with specific examples.

"""

from pathlib import Path

__all__ = ["MANDATORY_FILTER_EXAMPLES"]

ALIASES = {"values": '"1", "2", "3"', "value": "1", "inverse": "1"}

with open(Path(__file__).parent.joinpath("optional_filters.txt"), "r") as f:
    OPTIONAL_FILTER_EXAMPLES = [line.strip() for line in f.readlines()]

with open(Path(__file__).parent.joinpath("filters.txt"), "r") as f:
    _filters = []
    for line in f.readlines():
        if line.strip() in OPTIONAL_FILTER_EXAMPLES:
            continue
        for alias in ALIASES:
            if alias in line:
                line = line.replace(alias, ALIASES[alias])
        _filters.append(line)

    MANDATORY_FILTER_EXAMPLES = _filters
