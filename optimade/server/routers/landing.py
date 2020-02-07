""" OPTiMaDe landing page, rendered as a Jinja2 template. """

from starlette.routing import Router, Route
from optimade import __api_version__
from pathlib import Path
from starlette.templating import Jinja2Templates

from . import ENTRY_COLLECTIONS
from .utils import meta_values

template_dir = Path(__file__).parent.joinpath("static").resolve()
TEMPLATES = Jinja2Templates(directory=[template_dir])


async def landing(request):
    """ Show a human-readable landing page when the base URL is accessed. """

    meta = meta_values(str(request.url), 1, 1, more_data_available=False)

    context = {
        "request": request,
        "request_url": request.url,
        "api_version": __api_version__,
        "versioned_url": str(request.url) + meta.api_version + "/",
        "implementation": meta.implementation,
        "provider": meta.provider,
        "endpoints": list(ENTRY_COLLECTIONS.keys()) + ["info"],
    }

    return TEMPLATES.TemplateResponse("landing_page.html", context)


router = Router(routes=[Route("/", endpoint=landing)])
