import copy
from fastapi import Request, APIRouter
from fastapi.responses import Response

from .utils import BASE_URL_PREFIXES

router = APIRouter(redirect_slashes=True)


class CsvResponse(Response):
    media_type = "text/csv"

    def init_headers(self, *args, **kwargs):
        """ Patch for base class `init_headers` that adds the
        `header=present` content-type parameter without affecting
        the OpenAPI schema.

        """
        cached_charset = copy.deepcopy(self.charset)
        self.charset = "{self.charset}; header=present"
        return_vals = super().init_headers(*args, **kwargs)
        self.charset = cached_charset
        return return_vals


@router.get(
    "/versions", tags=["Versions"], response_class=CsvResponse,
)
def get_versions(request: Request):
    """Respond with the text/csv representation for the served versions."""
    version = BASE_URL_PREFIXES["major"].replace("/v", "")
    response = f"version\n{version}"
    return CsvResponse(content=response)
