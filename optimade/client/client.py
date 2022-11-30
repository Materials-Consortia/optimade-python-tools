"""This module implements OPTIMADE client functionality for:

- making web requests to filter and harvest resources from OPTIMADE APIs,
- query multiple providers simultaneously.

"""

import asyncio
import functools
import json
import time
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from urllib.parse import urlparse

# External deps that are only used in the client code
try:
    import httpx
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

    all_results: Dict[str, Dict[str, Dict[str, QueryResults]]] = defaultdict(dict)
    """A nested dictionary keyed by endpoint and OPTIMADE filter string that contains
    the results from each base URL for that particular filter.
    """

    count_results: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(dict)
    """A nested dictionary keyed by endpoint and OPTIMADE filter string that contains
    the number of results from each base URL for that particular filter.
    """

    max_results_per_provider: Optional[int] = None
    """Maximum number of results to downlod per provider. If None, will
    download all.
    """

    headers: Dict = {"User-Agent": f"optimade-python-tools/{__version__}"}
    """Additional HTTP headers."""

    http_timeout: int
    """The timeout to use for each HTTP request."""

    max_attempts: int
    """The maximum number of times to repeat a failed query before giving up."""

    use_async: bool
    """Whether or not to make all requests asynchronously using asyncio."""

    __current_endpoint: Optional[str] = None
    """Used internally when querying via `client.structures.get()` to set the
    chosen endpoint. Should be reset to `None` outside of all `get()` calls."""

    def __init__(
        self,
        base_urls: Optional[Union[str, Iterable[str]]] = None,
        max_results_per_provider: int = 1000,
        headers: Optional[Dict] = None,
        http_timeout: int = 10,
        max_attempts: int = 5,
        use_async: bool = True,
    ):
        """Create the OPTIMADE client object.

        Parameters:
            base_urls: A list of OPTIMADE base URLs to query.
            max_results_per_provider: The maximum number of results to download
                from each provider.
            headers: Any additional HTTP headers to use for the queries.
            http_timeout: The HTTP timeout to use per request.
            max_attempts: The maximum number of times to repeat a failing query.
            use_async: Whether or not to make all requests asynchronously.

        """

        self.max_results_per_provider = max_results_per_provider
        if self.max_results_per_provider in (-1, 0):
            self.max_results_per_provider = None

        if not base_urls:
            self.base_urls = get_all_databases()
        else:
            self.base_urls = base_urls

        if isinstance(self.base_urls, str):
            self.base_urls = [self.base_urls]
        self.base_urls = list(self.base_urls)

        if not self.base_urls:
            raise SystemExit(
                "Unable to access any OPTIMADE base URLs. If you believe this is an error, try manually specifying some base URLs."
            )

        if headers:
            self.headers.update(headers)

        self.http_timeout = http_timeout
        self.max_attempts = max_attempts

        self.use_async = use_async

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
        response_fields: Optional[List[str]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Dict[str, Dict[str, Dict]]]:
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

        self._check_filter(filter, endpoint)

        self._progress = OptimadeClientProgress()

        with self._progress:
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
            return {endpoint: {filter: {k: results[k].dict() for k in results}}}

    def count(
        self, filter: Optional[str] = None, endpoint: Optional[str] = None
    ) -> Dict[str, Dict[str, Dict[str, Optional[int]]]]:
        """Counts the number of results for the filter, requiring
        only 1 request per provider by making use of the `meta->data_returned`
        key.

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

        self._check_filter(filter, endpoint)

        self._progress = OptimadeClientProgress()
        with self._progress:
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
                response_fields=None,
                sort=None,
            )
            count_results = {}

            for base_url in results:
                count_results[base_url] = results[base_url].meta.get(
                    "data_returned", None
                )

                if count_results[base_url] is None:
                    self._progress.print(
                        f"Warning: {base_url} did not return a value for `meta->data_returned`, unable to count results."
                    )

            self.count_results[endpoint][filter] = count_results
            return {endpoint: {filter: count_results}}

    def _execute_queries(
        self,
        filter: str,
        endpoint: str,
        page_limit: Optional[int],
        paginate: bool,
        response_fields: Optional[List[str]],
        sort: Optional[str],
    ) -> Dict[str, QueryResults]:
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
                    self._progress.print(
                        "Detected a running event loop (e.g., Jupyter, pytest). Running in synchronous mode."
                    )
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
        response_fields: Optional[List[str]] = None,
        sort: Optional[str] = None,
        page_limit: Optional[int] = None,
        paginate: bool = True,
    ) -> Dict[str, QueryResults]:
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
            )
        except (RuntimeError, httpx.TimeoutException, json.JSONDecodeError) as exc:
            error_query_results = QueryResults()
            error_query_results.errors = [str(exc)]
            self._progress.print(
                f"[red]Error[/red]: Provider {str(base_url)!r} returned: [red i]{exc}[/red i]"
            )
            return {base_url: error_query_results}

    async def _get_all_async(
        self,
        endpoint: str,
        filter: str,
        response_fields: Optional[List[str]] = None,
        sort: Optional[str] = None,
        page_limit: Optional[int] = None,
        paginate: bool = True,
    ) -> Dict[str, QueryResults]:
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

        Returns:
            A dictionary mapping from base URL to the results of the query.

        """
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
                )
                for base_url in self.base_urls
            ]
        )
        return functools.reduce(lambda r1, r2: {**r1, **r2}, results)

    def _get_all(
        self,
        endpoint: str,
        filter: str,
        page_limit: Optional[int] = None,
        response_fields: Optional[List[str]] = None,
        sort: Optional[str] = None,
        paginate: bool = True,
    ) -> Dict[str, QueryResults]:
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

        Returns:
            A dictionary mapping from base URL to the results of the query.

        """
        results = [
            self.get_one(
                endpoint,
                filter,
                base_url,
                page_limit=page_limit,
                paginate=paginate,
                response_fields=response_fields,
                sort=sort,
            )
            for base_url in self.base_urls
        ]
        if results:
            return functools.reduce(lambda r1, r2: {**r1, **r2}, results)

        return {}

    async def get_one_async(
        self,
        endpoint: str,
        filter: str,
        base_url: str,
        response_fields: Optional[List[str]] = None,
        sort: Optional[str] = None,
        page_limit: Optional[int] = None,
        paginate: bool = True,
    ) -> Dict[str, QueryResults]:
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
            )
        except (
            RuntimeError,
            httpx.TimeoutException,
            json.JSONDecodeError,
            Exception,
        ) as exc:
            error_query_results = QueryResults()
            error_query_results.errors = [str(exc)]
            self._progress.print(
                f"[red]Error[/red]: Provider {str(base_url)!r} returned: [red i]{exc}[/red i]"
            )
            return {base_url: error_query_results}

    async def _get_one_async(
        self,
        endpoint: str,
        filter: str,
        base_url: str,
        response_fields: Optional[List[str]] = None,
        sort: Optional[str] = None,
        page_limit: Optional[int] = None,
        paginate: bool = True,
    ) -> Dict[str, QueryResults]:
        """See [`OptimadeClient.get_one_async`][optimade.client.OptimadeClient.get_one_async]."""
        next_url, _task = self._setup(
            endpoint=endpoint,
            base_url=base_url,
            filter=filter,
            page_limit=page_limit,
            response_fields=response_fields,
            sort=sort,
        )
        results = QueryResults()
        try:
            async with httpx.AsyncClient(headers=self.headers) as client:
                while next_url:

                    attempts = 0
                    try:
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
        response_fields: Optional[List[str]] = None,
        paginate: bool = True,
    ) -> Dict[str, QueryResults]:
        """See [`OptimadeClient.get_one`][optimade.client.OptimadeClient.get_one]."""
        next_url, _task = self._setup(
            endpoint=endpoint,
            base_url=base_url,
            filter=filter,
            page_limit=page_limit,
            response_fields=response_fields,
            sort=sort,
        )
        results = QueryResults()
        try:
            with httpx.Client(headers=self.headers) as client:
                while next_url:

                    attempts = 0
                    try:
                        r = client.get(
                            next_url, follow_redirects=True, timeout=self.http_timeout
                        )
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
        response_fields: Optional[List[str]],
        sort: Optional[str],
    ) -> Tuple[str, TaskID]:
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
        response_fields: Optional[List[str]] = None,
        sort: Optional[str] = None,
        page_limit: Optional[int] = None,
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

        Returns:
            The overall query URL, including parameters.

        """

        if not version:
            version = f'v{__api_version__.split(".")[0]}'
        while base_url.endswith("/"):
            base_url = base_url[:-1]

        url = f"{base_url}/{version}/{endpoint}"

        # Handle params
        _filter: Optional[str] = None
        _response_fields: Optional[str] = None
        _page_limit: Optional[str] = None
        _sort: Optional[str] = None

        if filter:
            _filter = f"filter={filter}"
        if response_fields:
            _response_fields = f'response_fields={",".join(response_fields)}'
        if page_limit:
            _page_limit = f"page_limit={page_limit}"
        if sort:
            _sort = f"sort={sort}"

        params = "&".join(
            p for p in (_filter, _response_fields, _page_limit, _sort) if p
        )
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
        self, response: httpx.Response, _task: TaskID
    ) -> Tuple[Dict[str, Any], str]:
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
                f"Could not decode response as JSON: {response.content}"
            ) from exc

        # Accumulate results with correct empty containers if missing
        results = {
            "data": r.get("data", []),
            "meta": r.get("meta", {}),
            "links": r.get("links", {}),
            "included": r.get("included", []),
            "errors": r.get("errors", []),
        }

        # Advance the progress bar for this provider
        self._progress.update(
            _task,
            advance=len(results["data"]),
            total=results["meta"].get("data_returned", None),
        )

        next_url = results["links"].get("next", None)
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
