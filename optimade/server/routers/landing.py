""" OPTIMADE landing page router. """

from functools import lru_cache
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse
from starlette.routing import Route, Router

from optimade import __api_version__
from optimade.server.config import CONFIG
from optimade.server.routers import ENTRY_COLLECTIONS
from optimade.server.routers.utils import get_base_url, meta_values


@lru_cache()
def render_landing_page(url: str) -> HTMLResponse:
    """Render and cache the landing page.

    This function uses the template file `./static/landing_page.html`, adapted
    from the original Jinja template. Instead of Jinja, some basic string
    replacement is used to fill out the fields from the server configuration.

    !!! warning "Careful"
        The removal of Jinja means that the fields are no longer validated as
        web safe before inclusion in the template.

    """
    meta = meta_values(url, 1, 1, more_data_available=False, schema=CONFIG.schema_url)
    major_version = __api_version__.split(".")[0]
    versioned_url = f"{get_base_url(url)}/v{major_version}/"

    template_dir = Path(__file__).parent.joinpath("static").resolve()

    html = (template_dir / "landing_page.html").read_text()

    # Build a dictionary that maps the old Jinja keys to the new simplified replacements
    replacements = {
        "api_version": __api_version__,
    }

    if meta.provider:
        replacements.update(
            {
                "provider.name": meta.provider.name,
                "provider.prefix": meta.provider.prefix,
                "provider.description": meta.provider.description,
                "provider.homepage": str(meta.provider.homepage) or "",
            }
        )

    if meta.implementation:
        replacements.update(
            {
                "implementation.name": meta.implementation.name or "",
                "implementation.version": meta.implementation.version or "",
                "implementation.source_url": str(meta.implementation.source_url or ""),
            }
        )

    for replacement in replacements:
        html = html.replace(f"{{{{ {replacement} }}}}", replacements[replacement])

    # Build the list of endpoints. The template already opens and closes the `<ul>` tag.
    endpoints_list = [
        f'<li><a href="{versioned_url}{endp}">{versioned_url}{endp}</a></li>'
        for endp in list(ENTRY_COLLECTIONS.keys()) + ["info"]
    ]
    html = html.replace("{% ENDPOINTS %}", "\n".join(endpoints_list))

    # If the index base URL has been configured, also list it
    index_base_url_html = ""
    if CONFIG.index_base_url:
        index_base_url_html = f"""<h3>Index base URL:</h3>
<p><a href={CONFIG.index_base_url}>{CONFIG.index_base_url}</a></p>
"""
    html = html.replace("{% INDEX_BASE_URL %}", index_base_url_html)

    return HTMLResponse(html)


async def landing(request: Request):
    """Show a human-readable landing page when the base URL is accessed."""
    return render_landing_page(str(request.url))


router = Router(routes=[Route("/", endpoint=landing)])
