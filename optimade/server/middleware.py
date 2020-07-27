from typing import Optional, IO, Type, Generator
import urllib.parse
import warnings

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from optimade.server.warnings import OptimadeWarning


class EnsureQueryParamIntegrity(BaseHTTPMiddleware):
    """Ensure all query parameters are followed by an equal sign (`=`)"""

    @staticmethod
    def check_url(url_query: str):
        """Check parsed URL query part for parameters not followed by `=`"""
        from optimade.server.exceptions import BadRequest

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
        import re

        from optimade.server.exceptions import VersionNotSupported
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
                        f"The parsed versioned base URL {version_prefix[0][0]!r} from {urllib.parse.urlunparse(parsed_url)!r} is not supported by this implementation. "
                        f"Supported versioned base URLs are: {', '.join(BASE_URL_PREFIXES.values())}"
                    )
                )

    async def dispatch(self, request: Request, call_next):
        parsed_url = urllib.parse.urlparse(str(request.url))
        if parsed_url.path:
            self.check_url(parsed_url)
        response = await call_next(request)
        return response


class AddWarnings(BaseHTTPMiddleware):
    """Add any raised `OptimadeWarning`s and subclasses thereof to the response meta.warnings"""

    def showwarning(
        self,
        message: Warning,
        category: Type[Warning],
        filename: str,
        lineno: int,
        file: Optional[IO] = None,
        line: Optional[str] = None,
    ) -> None:
        """Hook to write a warning to a file."""
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

        # Show warning message as normal in sys.stdout
        warnings._showwarnmsg_impl(
            warnings.WarningMessage(message, category, filename, lineno, file, line)
        )

    @staticmethod
    def chunk_it_up(content: str, chunk_size: int) -> Generator:
        """Return generator for string in chunks of size `chunk_size`"""
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
