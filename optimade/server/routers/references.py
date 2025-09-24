from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from optimade.models import (
    ReferenceResponseMany,
    ReferenceResponseOne,
)
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.routers.utils import get_entries, get_single_entry
from optimade.server.schemas import ERROR_RESPONSES

router = APIRouter(redirect_slashes=True)


@router.get(
    "/references",
    response_model=ReferenceResponseMany,
    response_model_exclude_unset=True,
    tags=["References"],
    responses=ERROR_RESPONSES,
)
def get_references(
    request: Request, params: Annotated[EntryListingQueryParams, Depends()]
) -> dict[str, Any]:
    references_coll = request.app.state.entry_collections.get("references")
    return get_entries(
        collection=references_coll,
        request=request,
        params=params,
    )


@router.get(
    "/references/{entry_id:path}",
    response_model=ReferenceResponseOne,
    response_model_exclude_unset=True,
    tags=["References"],
    responses=ERROR_RESPONSES,
)
def get_single_reference(
    request: Request,
    entry_id: str,
    params: Annotated[SingleEntryQueryParams, Depends()],
) -> dict[str, Any]:
    references_coll = request.app.state.entry_collections.get("references")
    return get_single_entry(
        collection=references_coll,
        entry_id=entry_id,
        request=request,
        params=params,
    )
