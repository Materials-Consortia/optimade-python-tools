from starlette.datastructures import URL
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse


class RedirectSlashedURLs(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """Redirect URL requests ending with a slash to non-slashed URLs

        E.g., `http://example.org/info/` -> `http://example.org/info`
        """
        if request.scope["path"].endswith("/"):
            redirect_scope = dict(request.scope)

            # Make sure we're not dealing with a URL path (after the domain) of `/`
            if redirect_scope["path"] != "/":
                redirect_scope["path"] = redirect_scope["path"][:-1]
                redirect_url = URL(scope=redirect_scope)
                return RedirectResponse(url=str(redirect_url))
        response = await call_next(request)
        return response
