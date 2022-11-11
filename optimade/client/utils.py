import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Set, Union

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

__all__ = (
    "RecoverableHTTPError",
    "TooManyRequestsException",
    "QueryResults",
    "OptimadeClientProgress",
)


class RecoverableHTTPError(Exception):
    """Base class for any HTTP issues that may be recoverable by just
    repeating the query."""


class TooManyRequestsException(RecoverableHTTPError):
    """For when the underlying HTTP request returns 429: Too Many Requests."""


@dataclass
class QueryResults:
    """A container dataclass for the results from a given query."""

    data: Union[Dict, List[Dict]] = field(default_factory=list, init=False)  # type: ignore[assignment]
    errors: List[str] = field(default_factory=list, init=False)
    links: Dict = field(default_factory=dict, init=False)
    included: List[Dict] = field(default_factory=list, init=False)
    meta: Dict = field(default_factory=dict, init=False)

    @property
    def included_index(self) -> Set[str]:
        if not getattr(self, "_included_index", None):
            self._included_index: Set[str] = set()
        return self._included_index

    def dict(self):
        return asdict(self)

    def update(self, page_results: Dict) -> None:
        """Combine the results from one page with the existing results for a given query.

        Parameters:
            page_results: The results for the current page.

        """

        if "data" in page_results:
            # If the `data` field is a list, add it to our existing results.
            # Otherwise, as is the case for `info` endpoints, `data` is a dictionary (or null)
            # and should be added as the only `data` field for these results.
            if isinstance(page_results["data"], list):
                self.data.extend(page_results["data"])  # type: ignore[union-attr]
            elif not self.data:
                self.data = page_results["data"]
            else:
                raise RuntimeError(
                    "Not overwriting old `data` field in `QueryResults`."
                )

        if "errors" in page_results:
            self.errors.extend(page_results["errors"])

        # Combine meta/links fields across all pages in a sensible way, i.e.,
        # if we really reached the last page of results, then make sure `links->next`
        # is null in the final response, and make sure `meta->more_data_available` is None or False.
        keys_to_filter = {
            "links": ("next", "prev"),
            "meta": ("query", "more_data_available"),
        }
        for top_level_key in keys_to_filter:
            if top_level_key not in page_results:
                page_results[top_level_key] = {}
            for k in keys_to_filter[top_level_key]:
                if k not in page_results[top_level_key]:
                    page_results[top_level_key][k] = None
            getattr(self, top_level_key).update(
                {k: page_results[top_level_key][k] for k in page_results[top_level_key]}
            )

        # Only add new unique entries to the included list
        for d in page_results.get("included", []):
            typed_id = f"{d['type']}/{d['id']}"
            if typed_id not in self.included_index:
                self.included_index.add(typed_id)
                self.included.append(d)


class OptimadeClientProgress(Progress):
    """A wrapper around `Rich.Progress` that defines the OPTIMADE client progressbars."""

    def __init__(self):
        super().__init__(
            SpinnerColumn(finished_text="[green]✓"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(
                text_format="[progress.completed]{task.completed}/[progress.total]{task.total}",
                text_format_no_percentage="[progress.completed]{task.completed}",
            ),
            TimeElapsedColumn(),
            console=Console(stderr=True),
            auto_refresh=True,
            refresh_per_second=10,
        )


@contextmanager
def silent_raise():
    """Raise an exception without printing a traceback, or the exception message itself."""
    default_value = getattr(
        sys, "tracebacklimit", 1000
    )  # `1000` is a Python's default value
    default_excepthook = getattr(sys, "excepthook")
    sys.tracebacklimit = 0
    sys.excepthook = lambda type, value, traceback: None
    yield
    sys.tracebacklimit = default_value  # revert changes
    sys.excepthook = default_excepthook
