from starlette.datastructures import URL
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from .routers import ENTRY_COLLECTIONS


class RedirectSlashedURLs(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """Redirect URL requests ending with a slash to non-slashed URLs

        E.g., `http://example.org/optimade/v0/info/` -> `http://example.org/optimade/v0/info`
        """
        if request.scope["path"].endswith("/") and any(
            request.scope["path"].endswith(f"{endpoint}/")
            for endpoint in list(ENTRY_COLLECTIONS.keys()) + ["info"]
        ):
            redirect_scope = dict(request.scope)
            redirect_scope["path"] = redirect_scope["path"][:-1]
            redirect_url = URL(scope=redirect_scope)
            return RedirectResponse(url=str(redirect_url))

        response = await call_next(request)
        return response
