from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from optimade.models import LinksResponse
from optimade.server.query_params import EntryListingQueryParams
from optimade.server.routers.utils import get_entries
from optimade.server.schemas import ERROR_RESPONSES

router = APIRouter(redirect_slashes=True)


@router.get(
    "/links",
    response_model=LinksResponse,
    response_model_exclude_unset=True,
    tags=["Links"],
    responses=ERROR_RESPONSES,
)
def get_links(
    request: Request, params: Annotated[EntryListingQueryParams, Depends()]
) -> dict[str, Any]:
    links_coll = request.app.state.entry_collections.get("links")

    return get_entries(collection=links_coll, request=request, params=params)
