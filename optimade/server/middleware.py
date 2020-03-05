import urllib.parse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from optimade.server.exceptions import BadRequest


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
