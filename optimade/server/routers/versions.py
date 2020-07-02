from fastapi import Request, APIRouter
from fastapi.responses import Response

from .utils import BASE_URL_PREFIXES

router = APIRouter(redirect_slashes=True)


@router.get(
    "/versions",
    tags=["Versions"],
    responses={
        200: {
            "description": "Successful Response",
            "content": {"text/csv": {"schema": {}}},
        }
    },
)
def get_versions(request: Request):
    """Respond with the text/csv representation for the served versions."""
    version = BASE_URL_PREFIXES["major"].replace("/v", "")
    response = f"version\n{version}"
    return Response(
        content=response, media_type="text/csv", headers={"header": "present"}
    )
