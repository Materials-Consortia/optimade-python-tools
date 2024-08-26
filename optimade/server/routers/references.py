from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from optimade.models import (
    ReferenceResource,
    ReferenceResponseMany,
    ReferenceResponseOne,
)
from optimade.server.config import CONFIG
from optimade.server.entry_collections import create_collection
from optimade.server.mappers import ReferenceMapper
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.routers.utils import get_entries, get_single_entry
from optimade.server.schemas import ERROR_RESPONSES

router = APIRouter(redirect_slashes=True)

references_coll = create_collection(
    name=CONFIG.references_collection,
    resource_cls=ReferenceResource,
    resource_mapper=ReferenceMapper,
)


@router.get(
    "/references",
    response_model=ReferenceResponseMany
    if CONFIG.validate_api_response
    else dict[str, Any],
    response_model_exclude_unset=True,
    tags=["References"],
    responses=ERROR_RESPONSES,
)
def get_references(
    request: Request, params: Annotated[EntryListingQueryParams, Depends()]
) -> dict[str, Any]:
    return get_entries(
        collection=references_coll,
        request=request,
        params=params,
    )


@router.get(
    "/references/{entry_id:path}",
    response_model=ReferenceResponseOne
    if CONFIG.validate_api_response
    else dict[str, Any],
    response_model_exclude_unset=True,
    tags=["References"],
    responses=ERROR_RESPONSES,
)
def get_single_reference(
    request: Request,
    entry_id: str,
    params: Annotated[SingleEntryQueryParams, Depends()],
) -> dict[str, Any]:
    return get_single_entry(
        collection=references_coll,
        entry_id=entry_id,
        request=request,
        params=params,
    )
