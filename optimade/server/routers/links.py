from typing import Any, Dict

from fastapi import APIRouter, Depends, Request

from optimade.models import LinksResource, LinksResponse
from optimade.server.config import CONFIG
from optimade.server.entry_collections import create_collection
from optimade.server.mappers import LinksMapper
from optimade.server.query_params import EntryListingQueryParams
from optimade.server.routers.utils import get_entries
from optimade.server.schemas import ERROR_RESPONSES

router = APIRouter(redirect_slashes=True)

links_coll = create_collection(
    name=CONFIG.links_collection,
    resource_cls=LinksResource,
    resource_mapper=LinksMapper,
)


@router.get(
    "/links",
    response_model=LinksResponse if CONFIG.validate_api_response else Dict,
    response_model_exclude_unset=True,
    tags=["Links"],
    responses=ERROR_RESPONSES,
)
def get_links(request: Request, params: EntryListingQueryParams = Depends()) -> Any:
    return get_entries(
        collection=links_coll, response=LinksResponse, request=request, params=params
    )
