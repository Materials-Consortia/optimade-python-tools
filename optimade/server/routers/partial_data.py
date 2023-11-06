from typing import Any

from fastapi import APIRouter, Depends, Request

from optimade.models import PartialDataResource  # type: ignore[attr-defined]
from optimade.server.config import CONFIG
from optimade.server.entry_collections import create_collection
from optimade.server.mappers import PartialDataMapper
from optimade.server.query_params import PartialDataQueryParams
from optimade.server.routers.utils import get_partial_entry
from optimade.server.schemas import ERROR_RESPONSES

router = APIRouter(redirect_slashes=True)

partial_data_coll = create_collection(
    name=CONFIG.partial_data_collection,
    resource_cls=PartialDataResource,
    resource_mapper=PartialDataMapper,
)


@router.get(
    "/partial_data/{entry_id:path}",
    response_model_exclude_unset=True,
    tags=["partial_data"],
    responses=ERROR_RESPONSES,
)
def get_partial_data(
    request: Request, entry_id: str, params: PartialDataQueryParams = Depends()
) -> Any:
    return get_partial_entry(
        collection=partial_data_coll,
        entry_id=entry_id,
        request=request,
        params=params,
    )
