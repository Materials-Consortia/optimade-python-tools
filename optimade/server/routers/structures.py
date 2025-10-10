from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from optimade.models import (
    StructureResponseMany,
    StructureResponseOne,
)
from optimade.server.config import ServerConfig
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.routers.utils import get_entries, get_single_entry
from optimade.server.schemas import ERROR_RESPONSES

router = APIRouter(redirect_slashes=True)

CONFIG = ServerConfig()


@router.get(
    "/structures",
    response_model=StructureResponseMany
    if CONFIG.validate_api_response
    else dict[str, Any],
    response_model_exclude_unset=True,
    tags=["Structures"],
    responses=ERROR_RESPONSES,
)
def get_structures(
    request: Request, params: Annotated[EntryListingQueryParams, Depends()]
) -> dict[str, Any]:
    structures_coll = request.app.state.entry_collections.get("structures")
    return get_entries(
        collection=structures_coll,
        request=request,
        params=params,
    )


@router.get(
    "/structures/{entry_id:path}",
    response_model=StructureResponseOne
    if CONFIG.validate_api_response
    else dict[str, Any],
    response_model_exclude_unset=True,
    tags=["Structures"],
    responses=ERROR_RESPONSES,
)
def get_single_structure(
    request: Request,
    entry_id: str,
    params: Annotated[SingleEntryQueryParams, Depends()],
) -> dict[str, Any]:
    structures_coll = request.app.state.entry_collections.get("structures")
    return get_single_entry(
        collection=structures_coll,
        entry_id=entry_id,
        request=request,
        params=params,
    )
