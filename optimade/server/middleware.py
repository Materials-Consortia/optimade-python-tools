import urllib.parse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


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
