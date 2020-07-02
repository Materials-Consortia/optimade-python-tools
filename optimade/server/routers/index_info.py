import urllib
from typing import Union

from fastapi import APIRouter, Request

from optimade import __api_version__

from optimade.models import (
    ErrorResponse,
    IndexInfoResponse,
    IndexInfoAttributes,
    IndexInfoResource,
    IndexRelationship,
    RelatedLinksResource,
)

from optimade.server.config import CONFIG

from optimade.server.routers.utils import meta_values, get_base_url


router = APIRouter(redirect_slashes=True)


@router.get(
    "/info",
    response_model=Union[IndexInfoResponse, ErrorResponse],
    response_model_exclude_unset=True,
    tags=["Info"],
)
def get_info(request: Request):

    parse_result = urllib.parse.urlparse(str(request.url))
    base_url = get_base_url(parse_result)

    return IndexInfoResponse(
        meta=meta_values(str(request.url), 1, 1, more_data_available=False),
        data=IndexInfoResource(
            id=IndexInfoResource.schema()["properties"]["id"]["const"],
            type=IndexInfoResource.schema()["properties"]["type"]["const"],
            attributes=IndexInfoAttributes(
                api_version=f"{__api_version__}",
                available_api_versions=[
                    {
                        "url": f"{base_url}/v{__api_version__.split('.')[0]}/",
                        "version": f"{__api_version__}",
                    }
                ],
                formats=["json"],
                available_endpoints=["info", "links"],
                entry_types_by_format={"json": []},
                is_index=True,
            ),
            relationships={
                "default": IndexRelationship(
                    data={
                        "type": RelatedLinksResource.schema()["properties"]["type"][
                            "const"
                        ],
                        "id": CONFIG.default_db,
                    }
                )
            },
        ),
    )
