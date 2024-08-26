import functools

from fastapi import APIRouter, Request
from fastapi.exceptions import StarletteHTTPException

from optimade import __api_version__
from optimade.models import EntryInfoResource, EntryInfoResponse, InfoResponse
from optimade.models.baseinfo import BaseInfoAttributes, BaseInfoResource
from optimade.server.config import CONFIG
from optimade.server.routers.utils import get_base_url, meta_values
from optimade.server.schemas import (
    ENTRY_INFO_SCHEMAS,
    ERROR_RESPONSES,
    retrieve_queryable_properties,
)

router = APIRouter(redirect_slashes=True)


@router.get(
    "/info",
    response_model=InfoResponse,
    response_model_exclude_unset=True,
    tags=["Info"],
    responses=ERROR_RESPONSES,
)
def get_info(request: Request) -> InfoResponse:
    @functools.lru_cache(maxsize=1)
    def _generate_info_response() -> BaseInfoResource:
        """Cached closure that generates the info response for the implementation."""

        return BaseInfoResource(
            id=BaseInfoResource.model_fields["id"].default,
            type=BaseInfoResource.model_fields["type"].default,
            attributes=BaseInfoAttributes(
                api_version=__api_version__,
                available_api_versions=[
                    {
                        "url": f"{get_base_url(request.url)}/v{__api_version__.split('.')[0]}",
                        "version": __api_version__,
                    }
                ],
                formats=["json"],
                available_endpoints=["info", "links"] + list(ENTRY_INFO_SCHEMAS.keys()),
                entry_types_by_format={"json": list(ENTRY_INFO_SCHEMAS.keys())},
                is_index=False,
            ),
        )

    return InfoResponse(
        meta=meta_values(
            request.url, 1, 1, more_data_available=False, schema=CONFIG.schema_url
        ),
        data=_generate_info_response(),
    )


@router.get(
    "/info/{entry}",
    response_model=EntryInfoResponse,
    response_model_exclude_unset=True,
    tags=["Info"],
    responses=ERROR_RESPONSES,
)
def get_entry_info(request: Request, entry: str) -> EntryInfoResponse:
    @functools.lru_cache(maxsize=len(ENTRY_INFO_SCHEMAS))
    def _generate_entry_info_response(entry: str) -> EntryInfoResource:
        """Cached closure that generates the entry info response for the given type.

        Parameters:
            entry: The OPTIMADE type to generate the info response for, e.g.,
                `"structures"`. Must be a key in `ENTRY_INFO_SCHEMAS`.

        """
        valid_entry_info_endpoints = ENTRY_INFO_SCHEMAS.keys()
        if entry not in valid_entry_info_endpoints:
            raise StarletteHTTPException(
                status_code=404,
                detail=(
                    f"Entry info not found for {entry}, valid entry info endpoints "
                    f"are: {', '.join(valid_entry_info_endpoints)}"
                ),
            )

        schema = ENTRY_INFO_SCHEMAS[entry]
        queryable_properties = {"id", "type", "attributes"}
        properties = retrieve_queryable_properties(
            schema, queryable_properties, entry_type=entry
        )

        output_fields_by_format = {"json": list(properties)}

        return EntryInfoResource(
            formats=list(output_fields_by_format),
            description=getattr(schema, "__doc__", "Entry Resources"),
            properties=properties,
            output_fields_by_format=output_fields_by_format,
        )

    return EntryInfoResponse(
        meta=meta_values(
            request.url, 1, 1, more_data_available=False, schema=CONFIG.schema_url
        ),
        data=_generate_entry_info_response(entry),
    )
