"""This module implements OPTIMADE client functionality for:

- making web requests to filter and harvest resources from OPTIMADE APIs,
- query multiple providers simultaneously.

"""

import asyncio
import functools
import json
import math
import time
from collections import defaultdict
from collections.abc import Iterable
from typing import Any, Callable, Optional, Union
from urllib.parse import urlparse

# External deps that are only used in the client code
try:
    import httpx
    import requests
    from rich.panel import Panel
    from rich.progress import TaskID
except ImportError as exc:
    raise ImportError(
        "Could not find dependencies required for the `OptimadeClient`. "
        "Please install them with `pip install .[http_client]` (if using a local repository) "
        "or `pip install optimade[http_client]` (if using the PyPI package)."
    ) from exc


from optimade import __api_version__, __version__
from optimade.client.utils import (
    OptimadeClientProgress,
    QueryResults,
    RecoverableHTTPError,
    TooManyRequestsException,
    silent_raise,
)
from optimade.exceptions import BadRequest
from optimade.filterparser import LarkParser
from optimade.utils import get_all_databases

ENDPOINTS = ("structures", "references", "calculations", "info", "extensions")

__all__ = ("OptimadeClient",)


class OptimadeClient:
    """This class implemements a client for executing the same queries
    across multiple OPTIMADE APIs simultaneously, paging and caching the
    results.

    By default, all registered OPTIMADE providers will be queried
    simulateneously and asynchronously, with the results collected
    into the `all_results` attribute, keyed by endpoint, filter
    and provider.

    """

    base_urls: Union[str, Iterable[str]]
    """A list (or any iterable) of OPTIMADE base URLs to query."""

    all_results: dict[str, dict[str, dict[str, QueryResults]]] = defaultdict(dict)
    """A nested dictionary keyed by endpoint and OPTIMADE filter string that contains
    the results from each base URL for that particular filter.
    """

    count_results: dict[str, dict[str, dict[str, int]]] = defaultdict(dict)
    """A nested dictionary keyed by endpoint and OPTIMADE filter string that contains
    the number of results from each base URL for that particular filter.
    """

    max_results_per_provider: Optional[int] = None
    """Maximum number of results to downlod per provider. If None, will
    download all.
    """

    property_lists: dict[str, dict[str, list[str]]] = defaultdict(dict)
    """A dictionary containing list of properties served by each database,
    broken down by entry type, then database.
    """

    headers: dict = {"User-Agent": f"optimade-python-tools/{__version__}"}
    """Additional HTTP headers."""

    http_timeout: httpx.Timeout = httpx.Timeout(10.0, read=1000.0)
    """The timeout to use for each HTTP request."""

    max_attempts: int
    """The maximum number of times to repeat a failed query before giving up."""

    use_async: bool
    """Whether or not to make all requests asynchronously using asyncio."""

    callbacks: Optional[list[Callable[[str, dict], Union[None, dict]]]] = None
    """A list of callbacks to execute after each successful request, used
    to e.g., write to a file, add results to a database or perform additional
    filtering.

    The callbacks will receive the request URL and the results extracted
    from the JSON response, with keys 'data', 'meta', 'links', 'errors'
    and 'included'.

    Each callback can return a dictionary that can modify the `next_url` with the
    key `next` and the progress bar with the key `advance_results`.
    In the case of multiple provided callbacks, only the value returned by the final
    callback in the stack will be used.

    """

    count_binary_search: bool = True
    """Enable binary search count for databases that do not support `meta->data_returned`."""

    silent: bool
    """Whether to disable progress bar printing."""

    skip_ssl: bool = False
    """Whether to skip SSL verification."""

    _excluded_providers: Optional[set[str]] = None
    """A set of providers IDs excluded from future queries."""

    _included_providers: Optional[set[str]] = None
    """A set of providers IDs included from future queries."""

    _excluded_databases: Optional[set[str]] = None
    """A set of child database URLs excluded from future queries."""

    __current_endpoint: Optional[str] = None
    """Used internally when querying via `client.structures.get()` to set the
    chosen endpoint. Should be reset to `None` outside of all `get()` calls."""

    _http_client: Optional[Union[type[httpx.AsyncClient], type[requests.Session]]] = (
        None
    )
    """Override the HTTP client class, primarily used for testing."""

    __strict_async: bool = False
    """Whether or not to fallover if `use_async` is true yet asynchronous mode
    is impossible due to, e.g., a running event loop.
    """

    _force_binary_search: bool = False
    """Setting to test binary searches in cases where servers do return
    the count.
    """

    def __init__(
        self,
        base_urls: Optional[Union[str, Iterable[str]]] = None,
        max_results_per_provider: int = 1000,
        headers: Optional[dict] = None,
        http_timeout: Optional[Union[httpx.Timeout, float]] = None,
        max_attempts: int = 5,
        use_async: bool = True,
        silent: bool = False,
        exclude_providers: Optional[list[str]] = None,
        include_providers: Optional[list[str]] = None,
        exclude_databases: Optional[list[str]] = None,
        http_client: Optional[
            Union[type[httpx.AsyncClient], type[requests.Session]]
        ] = None,
        verbosity: int = 0,
        callbacks: Optional[list[Callable[[str, dict], Union[None, dict]]]] = None,
        skip_ssl: bool = False,
    ):
        """Create the OPTIMADE client object.

        Parameters:
            base_urls: A list of OPTIMADE base URLs to query.
            max_results_per_provider: The maximum number of results to download
                from each provider (-1 or 0 indicate unlimited).
            headers: Any additional HTTP headers to use for the queries.
            http_timeout: The timeout to use per request. Defaults to 10
                seconds with 1000 seconds for reads specifically. Overriding this value
                will replace all timeouts (connect, read, write and pool) with this value.
            max_attempts: The maximum number of times to repeat a failing query.
            use_async: Whether or not to make all requests asynchronously.
            exclude_providers: A set or collection of provider IDs to exclude from queries.
            include_providers: A set or collection of provider IDs to include in queries.
            exclude_databases: A set or collection of child database URLs to exclude from queries.
            http_client: An override for the underlying HTTP client, primarily used for testing.
            callbacks: A list of functions to call after each successful response, see the
                attribute [`OptimadeClient.callbacks`][optimade.client.OptimadeClient.callbacks]
                docstring for more details.
            verbosity: The verbosity level of the client.

        """

        self.max_results_per_provider = max_results_per_provider
        if self.max_results_per_provider in (-1, 0):
            self.max_results_per_provider = None

        self._excluded_providers = set(exclude_providers) if exclude_providers else None
        self._included_providers = set(include_providers) if include_providers else None
        self._excluded_databases = set(exclude_databases) if exclude_databases else None

        self.max_attempts = max_attempts
        self.silent = silent
        self.verbosity = verbosity
        self.skip_ssl = skip_ssl

        if headers:
            self.headers.update(headers)

        if not base_urls:
            progress = None
            if not self.silent:
                progress = OptimadeClientProgress()
            self.base_urls = list(
                get_all_databases(
                    exclude_providers=self._excluded_providers,
                    include_providers=self._included_providers,
                    exclude_databases=self._excluded_databases,
                    progress=progress,
                    skip_ssl=self.skip_ssl,
                )
            )
        else:
            if exclude_providers or include_providers or exclude_databases:
                raise RuntimeError(
                    "Cannot provide both a list of base URLs and included/excluded databases."
                )

            self.base_urls = base_urls

            if isinstance(self.base_urls, str):
                self.base_urls = [self.base_urls]
            self.base_urls = list(self.base_urls)

        if not self.base_urls:
            raise SystemExit(
                "Unable to access any OPTIMADE base URLs. If you believe this is an error, try manually specifying some base URLs."
            )

        if http_timeout:
            if isinstance(http_timeout, httpx.Timeout):
                self.http_timeout = http_timeout
            else:
                self.http_timeout = httpx.Timeout(http_timeout)

        self.use_async = use_async

        if http_client:
            self._http_client = http_client
            if issubclass(self._http_client, httpx.AsyncClient):
                if not self.use_async and self.__strict_async:
                    raise RuntimeError(
                        "Cannot use synchronous mode with an asynchronous HTTP client, please set `use_async=True` or pass an asynchronous HTTP client."
                    )
                self.use_async = True
            elif issubclass(self._http_client, requests.Session):
                if self.use_async and self.__strict_async:
                    raise RuntimeError(
                        "Cannot use async mode with a synchronous HTTP client, please set `use_async=False` or pass an synchronous HTTP client."
                    )
                self.use_async = False
        else:
            if use_async:
                self._http_client = httpx.AsyncClient
            else:
                self._http_client = requests.Session

        self.callbacks = callbacks

    def __getattribute__(self, name):
        """Allows entry endpoints to be queried via attribute access, using the
        allowed list for this module.

        Should also pass through any `extensions/<example>` endpoints.

        Any non-entry-endpoint name requested will be passed to the
        original `__getattribute__`.

        !!! example
            ```python
            from optimade.client import OptimadeClient
            cli = OptimadeClient()
            structures = cli.structures.get()
            references = cli.references.get()
            info_structures = cli.info.structures.get()
            ```

        """
        if name in ENDPOINTS:
            if self.__current_endpoint == "info":
                self.__current_endpoint = f"info/{name}"
            elif self.__current_endpoint == "extensions":
                self.__current_endpoint = f"extensions/{name}"
            else:
                self.__current_endpoint = name
            return self

        return super().__getattribute__(name)

    def get(
        self,
        filter: Optional[str] = None,
        endpoint: Optional[str] = None,
        response_fields: Optional[list[str]] = None,
        sort: Optional[str] = None,
    ) -> dict[str, dict[str, dict[str, dict]]]:
        """Gets the results from the endpoint and filter across the
        defined OPTIMADE APIs.

        Parameters:
            filter: The OPTIMADE filter string for the query.
            endpoint: The endpoint to query.
            response_fields: A list of response fields to request
                from the server.
            sort: The field by which to sort the results.

        Raises:
            RuntimeError: If the query could not be executed.

        Returns:
            A nested mapping from endpoint, filter and base URL to the query results.

        """

        if endpoint is None:
            if self.__current_endpoint is not None:
                endpoint = self.__current_endpoint
                self.__current_endpoint = None
            else:
                endpoint = "structures"

        if filter is None:
            filter = ""

        self._progress = OptimadeClientProgress()
        if self.silent:
            self._progress.disable = True

        self._check_filter(filter, endpoint)

        with self._progress:
            if not self.silent:
                self._progress.print(
                    Panel(
                        f"Performing query [bold yellow]{endpoint}[/bold yellow]/?filter=[bold magenta][i]{filter}[/i][/bold magenta]",
                        expand=False,
                    )
                )
            results = self._execute_queries(
                filter,
                endpoint,
                response_fields=response_fields,
                page_limit=None,
                paginate=True,
                sort=sort,
            )
            self.all_results[endpoint][filter] = results
            return {endpoint: {filter: {k: results[k].asdict() for k in results}}}

    def count(
        self, filter: Optional[str] = None, endpoint: Optional[str] = None
    ) -> dict[str, dict[str, dict[str, Optional[int]]]]:
        """Counts the number of results for the filter, requiring
        only 1 request per provider by making use of the `meta->data_returned`
        key. If missing, attempts will be made to perform an exponential/binary
        search over pagination to count the results.

        Raises:
            RuntimeError: If the query could not be executed.

        Returns:
            A nested mapping from endpoint, filter and base URL to the number of query results.

        """

        if endpoint is None:
            if self.__current_endpoint is not None:
                endpoint = self.__current_endpoint
                self.__current_endpoint = None
            else:
                endpoint = "structures"

        if filter is None:
            filter = ""

        self._progress = OptimadeClientProgress()
        if self.silent:
            self._progress.disable = True

        self._check_filter(filter, endpoint)

        with self._progress:
            if not self.silent:
                self._progress.print(
                    Panel(
                        f"Counting results for [bold yellow]{endpoint}[/bold yellow]/?filter=[bold magenta][i]{filter}[/i][/bold magenta]",
                        expand=False,
                    )
                )
            results = self._execute_queries(
                filter,
                endpoint,
                page_limit=1,
                paginate=False,
                response_fields=[],
                sort=None,
            )
            count_results = {}

            for base_url in results:
                count_results[base_url] = results[base_url].meta.get(
                    "data_returned", None
                )

                if count_results[base_url] is None or self._force_binary_search:
                    if self.count_binary_search:
                        count_results[base_url] = self.binary_search_count(
                            filter, endpoint, base_url, results
                        )
                    else:
                        self._progress.print(
                            f"Warning: {base_url} did not return a value for `meta->data_returned`, unable to count results. Full response: {results[base_url]}"
                        )

            self.count_results[endpoint][filter] = count_results
            return {endpoint: {filter: count_results}}

    def binary_search_count(
        self, filter: str, endpoint: str, base_url: str, results: Optional[dict] = None
    ) -> int:
        """In cases where `data_returned` is not available (due to database limitations or
        otherwise), iteratively probe the final page of results available for a filter using
        binary search.

        Note: These queries always happen synchronously across APIs, but can be executed
        asynchronously within a single API.

        Parameters:
            filter: The OPTIMADE filter string for the query.
            endpoint: The endpoint to query.
            base_url: The base URL to query.
            results: The results from a previous query for the first page of results.

        Returns:
            The number of results for the filter.

        """
        if self.verbosity:
            self._progress.print(f"Performing binary search count for {base_url}")
        if self.use_async:
            return self._binary_search_count_async(filter, endpoint, base_url, results)

        else:
            raise NotImplementedError(
                "Binary search count is not yet implemented for synchronous queries."
            )

    def _binary_search_count_async(
        self, filter: str, endpoint: str, base_url: str, result: Optional[dict] = None
    ) -> int:
        """Run a series of asynchronously queries on a given API to
        find the number of results for a filter.

        Starting with logarithmically spaced page offsets, iteratively probe
        the final page of results available for a filter.

        Parameters:
            filter: The OPTIMADE filter string for the query.
            endpoint: The endpoint to query.
            base_url: The base URL to query.
            result: The results from a previous query for the first page of results.

        Returns:
            The number of results for the filter.

        """
        if result is None:
            # first a check that there are any results at all
            result = asyncio.run(
                self.get_one_async(
                    endpoint,
                    filter,
                    base_url,
                    page_limit=1,
                    response_fields=[],
                    paginate=False,
                )
            )
            if self.verbosity:
                self._progress.print("Definitely found results")

        if not result[base_url].data:
            return 0

        attempts = 0
        max_attempts = 100

        window, probe = self._update_probe_and_window()

        while attempts < max_attempts:
            self._progress.disable = True

            result = asyncio.run(
                self.get_one_async(
                    endpoint,
                    filter,
                    base_url,
                    page_limit=1,
                    response_fields=[],
                    paginate=False,
                    other_params={"page_offset": probe},
                )
            )

            self._progress.disable = self.silent

            window, probe = self._update_probe_and_window(
                window, probe, bool(result[base_url].data)
            )

            if window[0] == window[1] and window[0] == probe:
                return probe

            attempts += 1

            if self.verbosity > 2:
                self._progress.print(f"Binary search debug info: {window=}, {probe=}")

        else:
            message = f"Exceeded maximum number of attempts for binary search on {base_url}, {filter=}"
            self._progress.print(message)
            raise RuntimeError(message)

    @staticmethod
    def _update_probe_and_window(
        window: Optional[tuple[int, Optional[int]]] = None,
        last_probe: Optional[int] = None,
        below: Optional[bool] = None,
    ) -> tuple[tuple[int, Optional[int]], int]:
        """Sets the new range, trial value and exit condition for exponential/binary search.
        When converged, returns the same value three times.

        Parameters:
            window: The current window of results.
            last_probe: The last probe value.
            below: Whether the last probe was below the target value.

        Returns:
            A tuple of the new window and probe value,
            or the count three times if converged.

        """

        if window is None and last_probe is None:
            return (1, None), 1_000_000

        if window is None or last_probe is None:
            raise RuntimeError(
                "Invalid arguments: must provide all or none of window, last_probe and below parameters"
            )

        probe: int = last_probe

        # Exit condition: find a range of (count, count+1) values
        # and determine whether the probe was above or below in the last guess
        if window[1] is not None and window[1] - window[0] == 1:
            if below:
                return (window[0], window[0]), window[0]
            else:
                return (window[1], window[1]), window[1]

        # Enclose the real value in the window, with `None` indicating an open boundary
        if below:
            window = (last_probe, window[1])
        else:
            window = (window[0], last_probe)

        # If we've not reached the upper bound yet, try 10x
        if window[1] is None:
            probe *= 10

        # Otherwise, if we're in the window and the ends of the window now have the same power of 10, take the average (102 => 108) => 105
        elif round(math.log10(window[0])) == round(math.log10(window[0])):
            probe = (window[1] + window[0]) // 2
        # otherwise use logarithmic average (10, 1000) => 100
        else:
            probe = int(10 ** (math.log10(window[1]) + math.log10(window[0]) / 2))

        return window, probe

    def list_properties(
        self,
        entry_type: str,
    ) -> dict[str, list[str]]:
        """Returns the list of properties reported at `/info/<entry_type>`
        for the given entry type, for each database.

        """
        self._progress = OptimadeClientProgress()
        if self.silent:
            self._progress.disable = True

        with self._progress:
            if not self.silent:
                self._progress.print(
                    Panel(
                        f"Listing properties for [bold yellow]{entry_type}[/bold yellow]",
                        expand=False,
                    )
                )
            results = self._execute_queries(
                "",
                f"info/{entry_type}",
                paginate=False,
                page_limit=1,
                response_fields=[],
                sort=None,
            )
        self.property_lists = {entry_type: {}}
        for database in results:
            self.property_lists[entry_type][database] = list(
                results[database].data.get("properties", {}).keys()  # type: ignore
            )
        return self.property_lists[entry_type]

    def search_property(self, query: str, entry_type: str) -> dict[str, list[str]]:
        """Searches for the query substring within the listed properties
        served by each database.

        Parameters:
            query: The substring to search for.
            entry_type: The entry type to query.

        Returns:
            A nested dictionary of matching property lists, arranged by
            entry type and database.

        """
        if not self.property_lists:
            self.list_properties(entry_type=entry_type)

        matching_properties: dict[str, dict[str, list[str]]] = {
            entry_type: defaultdict(list)
        }
        if entry_type in self.property_lists:
            for database in self.property_lists[entry_type]:
                for property in self.property_lists[entry_type][database]:
                    if query in property:
                        matching_properties[entry_type][database].append(property)
        return matching_properties[entry_type]

    def _execute_queries(
        self,
        filter: str,
        endpoint: str,
        page_limit: Optional[int],
        paginate: bool,
        response_fields: Optional[list[str]],
        sort: Optional[str],
    ) -> dict[str, QueryResults]:
        """Executes the queries over the base URLs either asynchronously or
        serially, depending on the `self.use_async` setting.

        Parameters:
            filter: The OPTIMADE filter string.
            endpoint: The OPTIMADE endpoint to query.
            page_limit: A page limit to enforce for each query (used in
                conjunction with `paginate`).
            paginate: Whether to pull all pages of results (up to the
                value of `max_results_per_provider`) or whether to return
                after one page.
            response_fields: A list of response fields to request
                from the server.
            sort: The field by which to sort the results.

        Returns:
            A mapping from base URL to `QueryResults` for each queried API.

        """
        if self.use_async:
            # Check for a pre-existing event loop (e.g. within a Jupyter notebook)
            # and use it if present
            try:
                event_loop = asyncio.get_running_loop()
                if event_loop:
                    if self.__strict_async:
                        raise RuntimeError(
                            "Detected a running event loop, cannot run in async mode."
                        )
                    self._progress.print(
                        "Detected a running event loop (e.g., Jupyter). Attempting to switch to synchronous mode."
                    )
                    self.use_async = False
                    self._http_client = requests.Session
            except RuntimeError:
                event_loop = None

        if self.use_async and not event_loop:
            return asyncio.run(
                self._get_all_async(
                    endpoint,
                    filter,
                    page_limit=page_limit,
                    paginate=paginate,
                    response_fields=response_fields,
                    sort=sort,
                )
            )

        return self._get_all(
            endpoint,
            filter,
            page_limit=page_limit,
            paginate=paginate,
            response_fields=response_fields,
            sort=sort,
        )

    def get_one(
        self,
        endpoint: str,
        filter: str,
        base_url: str,
        response_fields: Optional[list[str]] = None,
        sort: Optional[str] = None,
        page_limit: Optional[int] = None,
        paginate: bool = True,
        other_params: Optional[dict[str, Any]] = None,
    ) -> dict[str, QueryResults]:
        """Executes the query synchronously on one API.

        Parameters:
            endpoint: The OPTIMADE endpoint to query.
            filter: The OPTIMADE filter string.
            response_fields: A list of response fields to request
                from the server.
            sort: The field by which to sort the results.
            page_limit: A page limit to enforce for each query (used in
                conjunction with `paginate`).
            paginate: Whether to pull all pages of results (up to the
                value of `max_results_per_provider`) or whether to return
                after one page.
            other_params: Any other parameters to pass to the server.

        Returns:
            A dictionary mapping from base URL to the results of the query.

        """
        try:
            return self._get_one(
                endpoint,
                filter,
                base_url,
                page_limit=page_limit,
                paginate=paginate,
                response_fields=response_fields,
                sort=sort,
                other_params=other_params,
            )
        except Exception as exc:
            error_query_results = QueryResults()
            error_query_results.errors = [
                f"{exc.__class__.__name__}: {str(exc.args[0])}"
            ]
            self._progress.print(
                f"[red]Error[/red]: Provider {str(base_url)!r} returned: [red i]{exc}[/red i]"
            )
            return {base_url: error_query_results}

    async def _get_all_async(
        self,
        endpoint: str,
        filter: str,
        response_fields: Optional[list[str]] = None,
        sort: Optional[str] = None,
        page_limit: Optional[int] = None,
        paginate: bool = True,
        base_urls: Optional[Iterable[str]] = None,
        other_params: Optional[dict[str, Any]] = None,
    ) -> dict[str, QueryResults]:
        """Executes the query asynchronously across all defined APIs.

        Parameters:
            endpoint: The OPTIMADE endpoint to query.
            filter: The OPTIMADE filter string.
            response_fields: A list of response fields to request
                from the server.
            sort: The field by which to sort the results.
            page_limit: A page limit to enforce for each query (used in
                conjunction with `paginate`).
            paginate: Whether to pull all pages of results (up to the
                value of `max_results_per_provider`) or whether to return
                after one page.
            base_urls: A list of base URLs to query (defaults to `self.base_urls`).
            other_params: Any other parameters to pass to the server.

        Returns:
            A dictionary mapping from base URL to the results of the query.

        """
        if not base_urls:
            base_urls = self.base_urls

        results = await asyncio.gather(
            *[
                self.get_one_async(
                    endpoint,
                    filter,
                    base_url,
                    page_limit=page_limit,
                    paginate=paginate,
                    response_fields=response_fields,
                    sort=sort,
                    other_params=other_params,
                )
                for base_url in base_urls
            ]
        )
        return functools.reduce(lambda r1, r2: {**r1, **r2}, results)

    def _get_all(
        self,
        endpoint: str,
        filter: str,
        page_limit: Optional[int] = None,
        response_fields: Optional[list[str]] = None,
        sort: Optional[str] = None,
        paginate: bool = True,
        base_urls: Optional[Iterable[str]] = None,
        other_params: Optional[dict[str, Any]] = None,
    ) -> dict[str, QueryResults]:
        """Executes the query synchronously across all defined APIs.

        Parameters:
            endpoint: The OPTIMADE endpoint to query.
            filter: The OPTIMADE filter string.
            response_fields: A list of response fields to request
                from the server.
            sort: The field by which to sort the results.
            page_limit: A page limit to enforce for each query (used in
                conjunction with `paginate`).
            paginate: Whether to pull all pages of results (up to the
                value of `max_results_per_provider`) or whether to return
                after one page.
            base_urls: A list of base URLs to query (defaults to `self.base_urls`).
            other_params: Any other parameters to pass to the server.

        Returns:
            A dictionary mapping from base URL to the results of the query.

        """
        if not base_urls:
            base_urls = self.base_urls
        results = [
            self.get_one(
                endpoint,
                filter,
                base_url,
                page_limit=page_limit,
                paginate=paginate,
                response_fields=response_fields,
                sort=sort,
                other_params=other_params,
            )
            for base_url in base_urls
        ]
        if results:
            return functools.reduce(lambda r1, r2: {**r1, **r2}, results)

        return {}

    async def get_one_async(
        self,
        endpoint: str,
        filter: str,
        base_url: str,
        response_fields: Optional[list[str]] = None,
        sort: Optional[str] = None,
        page_limit: Optional[int] = None,
        paginate: bool = True,
        other_params: Optional[dict[str, Any]] = None,
    ) -> dict[str, QueryResults]:
        """Executes the query asynchronously on one API.

        !!! note
            This method currently makes non-blocking requests
            to a single API, but these requests are executed
            serially on that API, i.e., results are pulled one
            page at a time, but requests will not block other
            async requests to other APIs.

        Parameters:
            endpoint: The OPTIMADE endpoint to query.
            filter: The OPTIMADE filter string.
            response_fields: A list of response fields to request
                from the server.
            sort: The field by which to sort the results.
            page_limit: A page limit to enforce for each query (used in
                conjunction with `paginate`).
            paginate: Whether to pull all pages of results (up to the
                value of `max_results_per_provider`) or whether to return
                after one page.
            other_params: Any other parameters to pass to the server.

        Returns:
            A dictionary mapping from base URL to the results of the query.

        """
        try:
            return await self._get_one_async(
                endpoint,
                filter,
                base_url,
                page_limit=page_limit,
                paginate=paginate,
                response_fields=response_fields,
                sort=sort,
                other_params=other_params,
            )
        except Exception as exc:
            error_query_results = QueryResults()
            error_query_results.errors = [
                f"{exc.__class__.__name__}: {str(exc.args[0])}"
            ]
            self._progress.print(
                f"[red]Error[/red]: Provider {str(base_url)!r} returned: [red i]{error_query_results.errors}[/red i]"
            )
            return {base_url: error_query_results}

    async def _get_one_async(
        self,
        endpoint: str,
        filter: str,
        base_url: str,
        response_fields: Optional[list[str]] = None,
        sort: Optional[str] = None,
        page_limit: Optional[int] = None,
        paginate: bool = True,
        other_params: Optional[dict[str, Any]] = None,
    ) -> dict[str, QueryResults]:
        """See [`OptimadeClient.get_one_async`][optimade.client.OptimadeClient.get_one_async]."""
        next_url, _task = self._setup(
            endpoint=endpoint,
            base_url=base_url,
            filter=filter,
            page_limit=page_limit,
            response_fields=response_fields,
            sort=sort,
            other_params=other_params,
        )
        results = QueryResults()
        try:
            async with self._http_client(headers=self.headers) as client:  # type: ignore[union-attr,call-arg,misc]
                while next_url:
                    attempts = 0
                    try:
                        if self.verbosity:
                            self._progress.print(
                                f"Making request to {next_url!r} {attempts=}"
                            )
                        r = await client.get(
                            next_url, follow_redirects=True, timeout=self.http_timeout
                        )
                        page_results, next_url = self._handle_response(r, _task)
                    except RecoverableHTTPError:
                        attempts += 1
                        if attempts > self.max_attempts:
                            raise RuntimeError(
                                f"Exceeded maximum number of retries for {next_url}"
                            )
                        await asyncio.sleep(1)
                        continue

                    results.update(page_results)

                    if not paginate:
                        break

                    if (
                        self.max_results_per_provider
                        and len(results.data) >= self.max_results_per_provider
                    ):
                        if not self.silent:
                            self._progress.print(
                                f"Reached {len(results.data)} results for {base_url}, exceeding `max_results_per_provider` parameter ({self.max_results_per_provider}). Stopping download."
                            )
                        break

            return {str(base_url): results}

        finally:
            self._teardown(_task, len(results.data))

    def _get_one(
        self,
        endpoint: str,
        filter: str,
        base_url: str,
        sort: Optional[str] = None,
        page_limit: Optional[int] = None,
        response_fields: Optional[list[str]] = None,
        paginate: bool = True,
        other_params: Optional[dict[str, Any]] = None,
    ) -> dict[str, QueryResults]:
        """See [`OptimadeClient.get_one`][optimade.client.OptimadeClient.get_one]."""
        next_url, _task = self._setup(
            endpoint=endpoint,
            base_url=base_url,
            filter=filter,
            page_limit=page_limit,
            response_fields=response_fields,
            sort=sort,
            other_params=other_params,
        )
        results = QueryResults()
        try:
            with self._http_client() as client:  # type: ignore[misc]
                client.headers.update(self.headers)

                if isinstance(client, requests.Session):
                    # Convert configured httpx timeout to requests-style tuple
                    timeout = (self.http_timeout.connect, self.http_timeout.read)

                while next_url:
                    attempts = 0
                    try:
                        if self.verbosity:
                            self._progress.print(
                                f"Making request to {next_url!r} {attempts=}"
                            )
                        r = client.get(next_url, timeout=timeout)
                        page_results, next_url = self._handle_response(r, _task)
                    except RecoverableHTTPError:
                        attempts += 1
                        if attempts > self.max_attempts:
                            raise RuntimeError(
                                f"Exceeded maximum number of retries for {next_url}"
                            )
                        time.sleep(1)
                        continue

                    results.update(page_results)

                    if (
                        self.max_results_per_provider
                        and len(results.data) >= self.max_results_per_provider
                    ):
                        if not self.silent:
                            self._progress.print(
                                f"Reached {len(results.data)} results for {base_url}, exceeding `max_results_per_provider` parameter ({self.max_results_per_provider}). Stopping download."
                            )
                        break

                    if not paginate:
                        break

            return {str(base_url): results}

        finally:
            self._teardown(_task, len(results.data))

    def _setup(
        self,
        endpoint: str,
        base_url: str,
        filter: str,
        page_limit: Optional[int],
        response_fields: Optional[list[str]],
        sort: Optional[str],
        other_params: Optional[dict[str, Any]] = None,
    ) -> tuple[str, TaskID]:
        """Constructs the first query URL and creates the progress bar task.

        Returns:
            The URL for the first query and the Rich TaskID for progress logging.

        """
        url = self._build_url(
            base_url=base_url,
            endpoint=endpoint,
            filter=filter,
            page_limit=page_limit,
            response_fields=response_fields,
            sort=sort,
            other_params=other_params,
        )
        parsed_url = urlparse(url)
        _task = self._progress.add_task(
            description=parsed_url.netloc + parsed_url.path,
            total=None,
        )
        return url, _task

    def _build_url(
        self,
        base_url: str,
        endpoint: Optional[str] = "structures",
        version: Optional[str] = None,
        filter: Optional[str] = None,
        response_fields: Optional[list[str]] = None,
        sort: Optional[str] = None,
        page_limit: Optional[int] = None,
        other_params: Optional[dict[str, Any]] = None,
    ) -> str:
        """Builds the URL to query based on the passed parameters.

        Parameters:
            base_url: The server's base URL.
            endpoint: The endpoint to query.
            version: The OPTIMADE version string.
            filter: The filter to apply to the endpoint.
            response_fields: A list of response fields to request from the server.
            sort: The field by which to sort the results.
            page_limit: The page limit for an individual request.
            other_params: Any other parameters to pass to the server.

        Returns:
            The overall query URL, including parameters.

        """

        if not version:
            version = f'v{__api_version__.split(".")[0]}'
        while base_url.endswith("/"):
            base_url = base_url[:-1]

        url = f"{base_url}/{version}/{endpoint}"

        params_dict: dict[str, str] = {}

        if filter:
            params_dict["filter"] = f"filter={filter}"
        if response_fields is not None:
            # If we have requested no response fields (e.g., in the case of --count) then just ask for IDs
            if len(response_fields) == 0:
                params_dict["response_fields"] = "response_fields=id"
            else:
                params_dict["response_fields"] = (
                    f'response_fields={",".join(response_fields)}'
                )

        if page_limit:
            params_dict["page_limit"] = f"page_limit={page_limit}"
        if sort:
            params_dict["sort"] = f"sort={sort}"

        if other_params:
            for p in other_params:
                params_dict[p] = f"{p}={other_params[p]}"

        params = "&".join(p for p in params_dict.values() if p)
        if params:
            url += f"?{params}"

        return url

    def _check_filter(self, filter: str, endpoint: str) -> None:
        """Passes the filter through [`LarkParser`][optimade.filterparser.LarkParser]
        from the optimade-python-tools reference server implementation.

        Parameters:
            filter: The filter string.
            endpoint: The endpoint being queried. If this endpoint is not "known" to
                OPTIMADE, the filter will automatically pass.

        Raises:
            RuntimeError: If the filter cannot be parsed.

        """
        try:
            if endpoint in ENDPOINTS:
                parser = LarkParser()
                parser.parse(filter)
        except BadRequest as exc:
            self._progress.print(
                f"[bold red]Filter [blue i]{filter!r}[/blue i] could not be parsed as an OPTIMADE filter.[/bold red]",
                Panel(f"[magenta]{exc}[/magenta]"),
            )
            with silent_raise():
                raise RuntimeError(exc) from None

    def _handle_response(
        self, response: Union[httpx.Response, requests.Response], _task: TaskID
    ) -> tuple[dict[str, Any], str]:
        """Handle the response from the server.

        Parameters:
            response: The response from the server.
            _task: The Rich TaskID for this task's progressbar.

        Returns:
            A dictionary containing the results, and a link to the next page,
            if it exists.

        """

        # Handle error statuses
        if response.status_code == 429:
            raise TooManyRequestsException(response.content)
        if response.status_code != 200:
            try:
                errors = response.json().get("errors")
                error_message = "\n".join(
                    [f"{error['title']}: {error['detail']}" for error in errors]
                )
            except Exception:
                error_message = str(response.content)

            raise RuntimeError(
                f"{response.status_code} - {response.url}: {error_message}"
            )

        try:
            r = response.json()
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Could not decode response as JSON: {response.content!r}"
            ) from exc

        # Accumulate results with correct empty containers if missing
        results = {
            "data": r.get("data", []),
            "meta": r.get("meta", {}),
            "links": r.get("links", {}),
            "included": r.get("included", []),
            "errors": r.get("errors", []),
        }

        callback_response = None
        if self.callbacks:
            callback_response = self._execute_callbacks(results, response)
        callback_response = callback_response or {}

        # Advance the progress bar for this provider
        self._progress.update(
            _task,
            advance=callback_response.get("advance_results", len(results["data"])),
            total=results["meta"].get("data_returned", None),
        )

        next_url = callback_response.get("next") or results["links"].get("next", None)
        if isinstance(next_url, dict):
            next_url = next_url.pop("href")

        return results, next_url

    def _teardown(self, _task: TaskID, num_results: int) -> None:
        """Update the finished status of the progress bar depending on the number of results.

        Parameters:
            _task: The Rich TaskID for this task's progressbar.
            num_results: The number of data entries returned.

        """
        if num_results == 0:
            self._progress.update(_task, total=None, finished=False, complete=True)
        else:
            self._progress.update(
                _task, total=num_results, finished=True, complete=True
            )

    def _execute_callbacks(
        self, results: dict, response: Union[httpx.Response, requests.Response]
    ) -> Union[None, dict]:
        """Execute any callbacks registered with the client.

        Parameters:
            results: The results from the query.
            response: The full response from the server.

        Returns:
            Either `None` or the string value returned from the *final* callback.

        """
        request_url = str(response.request.url)
        if not self.callbacks:
            return None
        for callback in self.callbacks:
            cb_response = callback(request_url, results)
        return cb_response
