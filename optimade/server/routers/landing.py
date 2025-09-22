"""OPTIMADE landing page router."""

from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse
from starlette.routing import Route, Router

from optimade import __api_version__
from optimade.server.config import ServerConfig
from optimade.server.routers.utils import get_base_url, meta_values

# In-process cache: {(config_id, url, custom_mtime): HTMLResponse}
_PAGE_CACHE: dict[tuple[int, str, float | None], HTMLResponse] = {}


def _custom_file_mtime(config: ServerConfig) -> float | None:
    custom = getattr(config, "custom_landing_page", None)
    if not custom:
        return None
    p = Path(custom)
    try:
        return p.resolve().stat().st_mtime
    except FileNotFoundError:
        return None


def render_landing_page(
    config: ServerConfig, entry_collections, url: str
) -> HTMLResponse:
    """Render and cache the landing page with a manual, hashable key."""
    cache_key = (id(config), url, _custom_file_mtime(config))
    cached = _PAGE_CACHE.get(cache_key)
    if cached is not None:
        return cached

    meta = meta_values(
        config, url, 1, 1, more_data_available=False, schema=config.schema_url
    )
    major_version = __api_version__.split(".")[0]
    versioned_url = f"{get_base_url(config, url)}/v{major_version}/"

    if config.custom_landing_page:
        html = Path(config.custom_landing_page).resolve().read_text()
    else:
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
                # avoid "None" string leaking into HTML
                "provider.homepage": str(meta.provider.homepage)
                if meta.provider.homepage
                else "",
            }
        )

    if meta.implementation:
        replacements.update(
            {
                "implementation.name": meta.implementation.name or "",
                "implementation.version": meta.implementation.version or "",
                "implementation.source_url": str(meta.implementation.source_url)
                if meta.implementation.source_url
                else "",
            }
        )

    for k, v in replacements.items():
        html = html.replace(f"{{{{ {k} }}}}", v)

    # Build the list of endpoints. The template already opens and closes the <ul> tag.
    endpoints_list = [
        f'<li><a href="{versioned_url}{endp}">{versioned_url}{endp}</a></li>'
        for endp in list(entry_collections.keys()) + ["info"]
    ]
    html = html.replace("{% ENDPOINTS %}", "\n".join(endpoints_list))

    # If the index base URL has been configured, also list it
    index_base_url_html = ""
    if config.index_base_url:
        index_base_url_html = f"""<h3>Index base URL:</h3>
<p><a href="{config.index_base_url}">{config.index_base_url}</a></p>
"""
    html = html.replace("{% INDEX_BASE_URL %}", index_base_url_html)

    resp = HTMLResponse(html)
    _PAGE_CACHE[cache_key] = resp
    return resp


async def landing(request: Request):
    """Show a human-readable landing page when the base URL is accessed."""
    config: ServerConfig = request.app.state.config
    entry_collections = request.app.state.entry_collections
    return render_landing_page(config, entry_collections, str(request.url))


router = Router(routes=[Route("/", endpoint=landing)])
