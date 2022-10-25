from fastapi import APIRouter, Request
from fastapi.exceptions import StarletteHTTPException

from optimade import __api_version__
from optimade.models import EntryInfoResponse, InfoResponse
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
    from optimade.models import BaseInfoAttributes, BaseInfoResource

    return InfoResponse(
        meta=meta_values(
            request.url, 1, 1, more_data_available=False, schema=CONFIG.schema_url
        ),
        data=BaseInfoResource(
            id=BaseInfoResource.schema()["properties"]["id"]["default"],
            type=BaseInfoResource.schema()["properties"]["type"]["default"],
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
        ),
    )


@router.get(
    "/info/{entry}",
    response_model=EntryInfoResponse,
    response_model_exclude_unset=True,
    tags=["Info"],
    responses=ERROR_RESPONSES,
)
def get_entry_info(request: Request, entry: str) -> EntryInfoResponse:
    from optimade.models import EntryInfoResource

    valid_entry_info_endpoints = ENTRY_INFO_SCHEMAS.keys()
    if entry not in valid_entry_info_endpoints:
        raise StarletteHTTPException(
            status_code=404,
            detail=f"Entry info not found for {entry}, valid entry info endpoints are: {', '.join(valid_entry_info_endpoints)}",
        )

    schema = ENTRY_INFO_SCHEMAS[entry]()
    queryable_properties = {"id", "type", "attributes"}
    properties = retrieve_queryable_properties(
        schema, queryable_properties, entry_type=entry
    )

    output_fields_by_format = {"json": list(properties.keys())}

    return EntryInfoResponse(
        meta=meta_values(
            request.url, 1, 1, more_data_available=False, schema=CONFIG.schema_url
        ),
        data=EntryInfoResource(
            formats=list(output_fields_by_format.keys()),
            description=schema.get("description", "Entry Resources"),
            properties=properties,
            output_fields_by_format=output_fields_by_format,
            schema=CONFIG.schema_url,
        ),
    )
