from typing import Union

from fastapi import APIRouter, Depends
from starlette.requests import Request

from optimade.models import ErrorResponse, LinksResponse, LinksResource
from optimade.server.config import CONFIG
from optimade.server.deps import EntryListingQueryParams
from optimade.server.entry_collections import MongoCollection, client
from optimade.server.mappers import LinksMapper

from .utils import get_entries

router = APIRouter()

links_coll = MongoCollection(
    collection=client[CONFIG.mongo_database][CONFIG.links_collection],
    resource_cls=LinksResource,
    resource_mapper=LinksMapper,
)


@router.get(
    "/links",
    response_model=Union[LinksResponse, ErrorResponse],
    response_model_exclude_unset=True,
    tags=["Links"],
)
def get_links(request: Request, params: EntryListingQueryParams = Depends()):
    for str_param in ["filter", "sort"]:
        if getattr(params, str_param):
            setattr(params, str_param, "")
    for int_param in [
        "page_offset",
        "page_page",
        "page_cursor",
        "page_above",
        "page_below",
    ]:
        if getattr(params, int_param):
            setattr(params, int_param, 0)
    params.page_limit = CONFIG.page_limit
    return get_entries(
        collection=links_coll, response=LinksResponse, request=request, params=params
    )
