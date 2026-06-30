from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from optimade.models import (
    FileResponseMany,
    FileResponseOne,
)
from optimade.server.config import ServerConfig
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.routers.utils import get_entries, get_single_entry
from optimade.server.schemas import ERROR_RESPONSES

router = APIRouter(redirect_slashes=True)

CONFIG = ServerConfig()


@router.get(
    "/files",
    response_model=FileResponseMany if CONFIG.validate_api_response else dict[str, Any],
    response_model_exclude_unset=True,
    tags=["Files"],
    responses=ERROR_RESPONSES,
)
def get_files(
    request: Request, params: Annotated[EntryListingQueryParams, Depends()]
) -> dict[str, Any]:
    files_coll = request.app.state.entry_collections.get("files")
    return get_entries(
        collection=files_coll,
        request=request,
        params=params,
    )


@router.get(
    "/files/{entry_id:path}",
    response_model=FileResponseOne if CONFIG.validate_api_response else dict[str, Any],
    response_model_exclude_unset=True,
    tags=["Files"],
    responses=ERROR_RESPONSES,
)
def get_single_file(
    request: Request,
    entry_id: str,
    params: Annotated[SingleEntryQueryParams, Depends()],
) -> dict[str, Any]:
    files_coll = request.app.state.entry_collections.get("files")
    return get_single_entry(
        collection=files_coll,
        entry_id=entry_id,
        request=request,
        params=params,
    )
