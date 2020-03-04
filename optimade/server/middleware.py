import urllib.parse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from optimade.server.routers.utils import BadRequest


class EnsureQueryParamIntegrity(BaseHTTPMiddleware):
    """Ensure all query parameters are followed by an equal sign (`=`)"""

    async def dispatch(self, request: Request, call_next):
        parsed_url = urllib.parse.urlsplit(str(request.url))
        if parsed_url.query:
            queries_amp = set(parsed_url.query.split("&"))
            queries = set()
            for query in queries_amp:
                queries.update(set(query.split(";")))
            queries = list(queries)
            for query in queries:
                if "=" not in query:
                    raise BadRequest(
                        detail="A query parameter without an equal sign (=) is not supported by this server"
                    )
        response = await call_next(request)
        return response
