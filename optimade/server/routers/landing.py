""" OPTIMADE landing page, rendered as a Jinja2 template. """

from pathlib import Path
from fastapi.templating import Jinja2Templates
from starlette.routing import Router, Route
from optimade import __api_version__

from optimade.server.routers import ENTRY_COLLECTIONS
from optimade.server.routers.utils import meta_values
from optimade.server.config import CONFIG

template_dir = Path(__file__).parent.joinpath("static").resolve()
TEMPLATES = Jinja2Templates(directory=[template_dir])


async def landing(request):
    """ Show a human-readable landing page when the base URL is accessed. """

    meta = meta_values(str(request.url), 1, 1, more_data_available=False)

    major_version = __api_version__.split(".")[0]
    versioned_url = (
        f"{request.url}"
        if f"v{major_version}" in f"{request.url.path}"
        else f"{request.url}v{major_version}/"
    )

    context = {
        "request": request,
        "request_url": request.url,
        "api_version": __api_version__,
        "implementation": meta.implementation,
        "versioned_url": versioned_url,
        "provider": meta.provider,
        "index_base_url": CONFIG.index_base_url,
        "endpoints": list(ENTRY_COLLECTIONS.keys()) + ["info"],
    }

    return TEMPLATES.TemplateResponse("landing_page.html", context)


router = Router(routes=[Route("/", endpoint=landing)])
