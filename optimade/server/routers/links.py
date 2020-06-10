from typing import Union

from fastapi import APIRouter, Depends, Request

from optimade.models import ErrorResponse, LinksResponse, LinksResource
from optimade.server.config import CONFIG
from optimade.server.entry_collections import MongoCollection, client
from optimade.server.mappers import LinksMapper
from optimade.server.query_params import EntryListingQueryParams

from .utils import get_entries

router = APIRouter(redirect_slashes=True)
router_index = APIRouter(redirect_slashes=True)

links_coll = MongoCollection(
    collection=client[CONFIG.mongo_database][CONFIG.links_collection],
    resource_cls=LinksResource,
    resource_mapper=LinksMapper,
)
index_links_coll = MongoCollection(
    collection=client[CONFIG.mongo_database][CONFIG.index_links_collection],
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
    return get_entries(
        collection=links_coll, response=LinksResponse, request=request, params=params
    )


@router_index.get(
    "/links",
    response_model=Union[LinksResponse, ErrorResponse],
    response_model_exclude_unset=True,
    tags=["Links"],
)
def get_index_links(request: Request, params: EntryListingQueryParams = Depends()):
    return get_entries(
        collection=index_links_coll,
        response=LinksResponse,
        request=request,
        params=params,
    )
