import re
from typing import Optional, IO, Type, Generator, List, Union
import urllib.parse
import warnings

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from optimade.server.exceptions import BadRequest, VersionNotSupported
from optimade.server.warnings import OptimadeWarning


class EnsureQueryParamIntegrity(BaseHTTPMiddleware):
    """Ensure all query parameters are followed by an equal sign (`=`)"""

    @staticmethod
    def check_url(url_query: str):
        """Check parsed URL query part for parameters not followed by `=`"""
        queries_amp = set(url_query.split("&"))
        queries = set()
        for query in queries_amp:
            queries.update(set(query.split(";")))
        for query in queries:
            if "=" not in query and query != "":
                raise BadRequest(
                    detail="A query parameter without an equal sign (=) is not supported by this server"
                )
        return queries  # Useful for testing

    async def dispatch(self, request: Request, call_next):
        parsed_url = urllib.parse.urlsplit(str(request.url))
        if parsed_url.query:
            self.check_url(parsed_url.query)
        response = await call_next(request)
        return response


class CheckWronglyVersionedBaseUrls(BaseHTTPMiddleware):
    """If a non-supported versioned base URL is supplied return `553 Version Not Supported`"""

    @staticmethod
    def check_url(parsed_url: urllib.parse.ParseResult):
        """Check URL path for versioned part"""
        from optimade.server.routers.utils import get_base_url, BASE_URL_PREFIXES

        base_url = get_base_url(parsed_url)
        optimade_path = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"[
            len(base_url) :
        ]
        if re.match(r"^/v[0-9]+", optimade_path):
            for version_prefix in BASE_URL_PREFIXES.values():
                if optimade_path.startswith(f"{version_prefix}/"):
                    break
            else:
                version_prefix = re.findall(r"(/v[0-9]+(\.[0-9]+){0,2})", optimade_path)
                raise VersionNotSupported(
                    detail=(
                        f"The parsed versioned base URL {version_prefix[0][0]!r} from "
                        f"{urllib.parse.urlunparse(parsed_url)!r} is not supported by this implementation. "
                        f"Supported versioned base URLs are: {', '.join(BASE_URL_PREFIXES.values())}"
                    )
                )

    async def dispatch(self, request: Request, call_next):
        parsed_url = urllib.parse.urlparse(str(request.url))
        if parsed_url.path:
            self.check_url(parsed_url)
        response = await call_next(request)
        return response


class HandleApiHint(BaseHTTPMiddleware):
    """Handle `api_hint` query parameter"""

    @staticmethod
    def handle_api_hint(api_hint: List[str]) -> Union[None, str]:
        """Handle `api_hint` parameter"""
        from optimade.server.routers.utils import BASE_URL_PREFIXES

        if len(api_hint) > 1:
            # TODO: Warning:
            # detail="`api_hint` should only be supplied once, with a single value."
            return None

        api_hint = f"/{api_hint[0]}"
        if re.match(r"^/v[0-9]+(\.[0-9]+)?$", api_hint) is None:
            # TODO: Warning:
            # detail=f"{api_hint[1:]!r} is not recognized as a valid `api_hint` value."
            return None

        if api_hint in BASE_URL_PREFIXES.values():
            return api_hint

        major_api_hint = int(re.findall(r"/v([0-9]+)", api_hint)[0])
        major_implementation = int(BASE_URL_PREFIXES["major"][len("/v") :])

        if major_api_hint > major_implementation:
            # Let's not try to handle a request for a newer major version
            raise VersionNotSupported(
                detail=(
                    f"The provided `api_hint` ({api_hint[1:]!r}) is not supported by this implementation. "
                    f"Supported versions include: {', '.join(BASE_URL_PREFIXES.values())}"
                )
            )
        if major_api_hint <= major_implementation:
            # If less than:
            # Use the current implementation in hope that it can still handle older requests
            #
            # If equal:
            # Go to /v<MAJOR>, since this should point to the latest available
            return BASE_URL_PREFIXES["major"]

    @staticmethod
    def is_versioned_base_url(url: str) -> bool:
        """Determine whether a URL is for a versioned base URL

        First, simply check whether a `/vMAJOR(.MINOR.PATCH)` part exists in the URL.
        If not, return False.
        Else, remove unversioned base URL from URL and check again.
        Return bool of final result.
        """
        from optimade.server.routers.utils import get_base_url

        if not re.findall(r"(/v[0-9]+(\.[0-9]+){0,2})", url):
            return False

        base_url = get_base_url(urllib.parse.urlparse(url))
        return bool(re.findall(r"(/v[0-9]+(\.[0-9]+){0,2})", url[len(base_url) :]))

    async def dispatch(self, request: Request, call_next):
        parsed_query = urllib.parse.parse_qs(request.url.query, keep_blank_values=True)

        if "api_hint" in parsed_query:
            if self.is_versioned_base_url(str(request.url)):
                # If this is a versioned base URL, don't handle `api_hint`, but add a warning
                # TODO: Warning:
                # detail=(
                #     f"`api_hint` provided with value(s) {\"', '\".parsed_query['api_hint']!r} for a versioned base URL. "
                #     "According with the specification, this will not be handled by the implementation."
                # )
                pass
            else:
                from optimade.server.routers.utils import get_base_url

                version_path = self.handle_api_hint(parsed_query["api_hint"])
                base_url = get_base_url(request.url)

                new_request = (
                    f"{base_url}{version_path}{str(request.url)[len(base_url):]}"
                )
                path = urllib.parse.urlsplit(new_request).path
                return RedirectResponse(
                    request.url.replace(path=path), headers=request.headers
                )
                # This is the non-URL changing solution:
                #
                # scope = request.scope
                # scope["path"] = path
                # request = Request(scope=scope, receive=request.receive, send=request._send)

        response = await call_next(request)
        return response


class AddWarnings(BaseHTTPMiddleware):
    """
    Add [`OptimadeWarning`][optimade.server.warnings.OptimadeWarning]s to the response.

    All sub-classes of [`OptimadeWarning`][optimade.server.warnings.OptimadeWarning]
    will also be added to the response's `meta.warnings` list.

    By overriding the `warnings.showwarning()` function with the
    [showwarning method][optimade.server.middleware.AddWarnings.showwarning],
    all usages of `warnings.warn()` will result in the regular printing of the
    warning message to `stderr`, but also its addition to an in-memory list of
    warnings.
    This middleware will, after the URL request has been handled, add the list of
    accumulated warnings to the JSON response under the `meta.warnings` field.

    To make sure the last part happens correctly and a Starlette `StreamingResponse`
    is returned, as is expected from a `BaseHTTPMiddleware` sub-class, one is
    instantiated with the updated `Content-Length` header, as well as making sure
    the response's body content is actually streamable, by breaking it down into
    chunks of the original response's chunk size.

    Attributes:
        _warnings (List[Warnings]): List of [Warnings][optimade.models.optimade_json.Warnings]
            added through usages of `warnings.warn()` via [showwarning][optimade.server.middleware.AddWarnings.showwarning].

    """

    def showwarning(
        self,
        message: Warning,
        category: Type[Warning],
        filename: str,
        lineno: int,
        file: Optional[IO] = None,
        line: Optional[str] = None,
    ) -> None:
        """
        Hook to write a warning to a file using the built-in `warnings` lib.

        In [the documentation](https://docs.python.org/3/library/warnings.html)
        for the built-in `warnings` library, there are a few recommended ways of
        customizing the printing of warning messages.

        This method can override the `warnings.showwarning` function,
        which is called as part of the `warnings` library's workflow to print
        warning messages, e.g., when using `warnings.warn()`.
        Originally, it prints warning messages to `stderr`.
        This method will also print warning messages to `stderr` by calling
        `warnings._showwarning_orig()` or `warnings._showwarnmsg_impl()`.
        The first function will be called if the issued warning is not recognized
        as an [`OptimadeWarning`][optimade.server.warnings.OptimadeWarning].'
        This is equivalent to "standard behaviour".
        The second function will be called _after_ an
        [`OptimadeWarning`][optimade.server.warnings.OptimadeWarning] has been handled.

        An [`OptimadeWarning`][optimade.server.warnings.OptimadeWarning] will be
        translated into an OPTIMADE Warnings JSON object in accordance with
        [the specification](https://github.com/Materials-Consortia/OPTIMADE/blob/v1.0.0/optimade.rst#json-response-schema-common-fields).
        This process is similar to the [Exception handlers][optimade.server.exception_handlers].

        Parameters:
            message (Warning): The `Warning` object to show and possibly handle.
            category (Type[Warning]): `Warning` type being warned about. This amounts to `type(message)`.
            filename (str): Name of the file, where the warning was issued.
            lineno (int): Line number in the file, where the warning was issued.
            file (Optional[IO]): A file-like object to which the warning should be written.
            line (Optional[str]): Source content of the line that issued the warning.

        """
        from optimade.models import Warnings
        from optimade.server.config import CONFIG

        assert isinstance(
            message, Warning
        ), "'message' is expected to be a Warning or subclass thereof."

        if not isinstance(message, OptimadeWarning):
            # If the Warning is not an OptimadeWarning or subclass thereof,
            # use the regular 'showwarning' function.
            warnings._showwarning_orig(message, category, filename, lineno, file, line)
            return

        # Format warning
        try:
            title = str(message.title)
        except AttributeError:
            title = str(message.__class__.__name__)

        try:
            detail = str(message.detail)
        except AttributeError:
            detail = str(message)

        if CONFIG.debug:
            if line is None:
                # All this is taken directly from the warnings library.
                # See 'warnings._formatwarnmsg_impl()' for the original code.
                try:
                    import linecache

                    line = linecache.getline(filename, lineno)
                except Exception:
                    # When a warning is logged during Python shutdown, linecache
                    # and the import machinery don't work anymore
                    line = None
                    linecache = None
            meta = {
                "filename": filename,
                "lineno": lineno,
            }
            if line:
                meta["line"] = line.strip()

        if CONFIG.debug:
            new_warning = Warnings(title=title, detail=detail, meta=meta)
        else:
            new_warning = Warnings(title=title, detail=detail)

        # Add new warning to self._warnings
        self._warnings.append(new_warning.dict(exclude_unset=True))

        # Show warning message as normal in sys.stderr
        warnings._showwarnmsg_impl(
            warnings.WarningMessage(message, category, filename, lineno, file, line)
        )

    @staticmethod
    def chunk_it_up(content: str, chunk_size: int) -> Generator:
        """
        Return generator for string in chunks of size `chunk_size`

        Parameters:
            content (str): String-content to separate into chunks.
            chunk_size (int): The size of the chunks, i.e. the length of the string-chunks.

        """
        return (content[i : chunk_size + i] for i in range(0, len(content), chunk_size))

    async def dispatch(self, request: Request, call_next):
        from starlette.responses import StreamingResponse

        try:
            import simplejson as json
        except ImportError:
            import json

        self._warnings = []

        warnings.simplefilter(action="default", category=OptimadeWarning)
        warnings.showwarning = self.showwarning

        response = await call_next(request)

        status = response.status_code
        headers = response.headers
        media_type = response.media_type
        background = response.background
        charset = response.charset

        body = b""
        first_run = True
        async for chunk in response.body_iterator:
            if first_run:
                first_run = False
                chunk_size = len(chunk)
            if not isinstance(chunk, bytes):
                chunk = chunk.encode(charset)
            body += chunk
        body = body.decode(charset)

        if self._warnings:
            response = json.loads(body)
            response.get("meta", {})["warnings"] = self._warnings
            body = json.dumps(response)
            if "content-length" in headers:
                headers["content-length"] = str(len(body))

        response = StreamingResponse(
            content=self.chunk_it_up(body, chunk_size),
            status_code=status,
            headers=headers,
            media_type=media_type,
            background=background,
        )

        return response
