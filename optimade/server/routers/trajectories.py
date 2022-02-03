from fastapi import APIRouter, Depends, Request

from optimade.models.trajectories import TrajectoryResource
from optimade.models import (
    TrajectoryResponseMany,
    TrajectoryResponseOne,
)
from optimade.server.config import CONFIG
from optimade.server.entry_collections import create_collection
from optimade.server.mappers import TrajectoryMapper
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.routers.utils import get_entries, get_single_entry
from optimade.server.schemas import ERROR_RESPONSES

router = APIRouter(redirect_slashes=True)

trajectories_coll = create_collection(
    name=CONFIG.trajectories_collection,
    resource_cls=TrajectoryResource,
    resource_mapper=TrajectoryMapper,
)


@router.get(
    "/trajectories",
    response_model=TrajectoryResponseMany,
    response_model_exclude_unset=True,
    tags=["Trajectories"],
    responses=ERROR_RESPONSES,
)
def get_trajectories(
    request: Request, params: EntryListingQueryParams = Depends()
) -> TrajectoryResponseMany:
    return get_entries(
        collection=trajectories_coll,
        response=TrajectoryResponseMany,
        request=request,
        params=params,
    )


@router.get(
    "/trajectories/{entry_id:path}",
    response_model=TrajectoryResponseOne,
    response_model_exclude_unset=True,
    tags=["Trajectories"],
    responses=ERROR_RESPONSES,
)
def get_single_structure(
    request: Request, entry_id: str, params: SingleEntryQueryParams = Depends()
) -> TrajectoryResponseOne:
    return get_single_entry(
        collection=trajectories_coll,
        entry_id=entry_id,
        response=TrajectoryResponseOne,
        request=request,
        params=params,
    )
