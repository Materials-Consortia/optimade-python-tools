from fastapi import APIRouter, Depends, Request

from optimade.models import (
    FileResource,
    FileResponseMany,
    FileResponseOne,
)
from optimade.server.config import CONFIG
from optimade.server.entry_collections import create_collection
from optimade.server.mappers import FileMapper
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.routers.utils import get_entries, get_single_entry
from optimade.server.schemas import ERROR_RESPONSES

router = APIRouter(redirect_slashes=True)

files_coll = create_collection(
    name=CONFIG.files_collection,
    resource_cls=FileResource,
    resource_mapper=FileMapper,
)


@router.get(
    "/files",
    response_model=FileResponseMany,
    response_model_exclude_unset=True,
    tags=["Files"],
    responses=ERROR_RESPONSES,
)
def get_files(
    request: Request, params: EntryListingQueryParams = Depends()
) -> FileResponseMany:
    return get_entries(
        collection=files_coll,
        response=FileResponseMany,
        request=request,
        params=params,
    )


@router.get(
    "/files/{entry_id:path}",
    response_model=FileResponseOne,
    response_model_exclude_unset=True,
    tags=["Files"],
    responses=ERROR_RESPONSES,
)
def get_single_file(
    request: Request, entry_id: str, params: SingleEntryQueryParams = Depends()
) -> FileResponseOne:
    return get_single_entry(
        collection=files_coll,
        entry_id=entry_id,
        response=FileResponseOne,
        request=request,
        params=params,
    )
