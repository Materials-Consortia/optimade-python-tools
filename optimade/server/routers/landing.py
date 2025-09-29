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
    path = getattr(config, "custom_landing_page", None)
    if not path:
        return None
    try:
        return Path(path).resolve().stat().st_mtime
    except FileNotFoundError:
        return None


def render_landing_page(
    config: ServerConfig, entry_collections, url: str
) -> HTMLResponse:
    """Render and cache the landing page with a manual, hashable key."""
    cache_key = (id(config), url, _custom_file_mtime(config))
    if cache_key in _PAGE_CACHE:
        return _PAGE_CACHE[cache_key]

    meta = meta_values(
        config, url, 1, 1, more_data_available=False, schema=config.schema_url
    )
    major_version = __api_version__.split(".")[0]
    versioned_url = f"{get_base_url(config, url)}/v{major_version}/"

    if config.custom_landing_page:
        html = Path(config.custom_landing_page).resolve().read_text()
    else:
        html = (
            (Path(__file__).parent / "static/landing_page.html").resolve().read_text()
        )

    replacements = {"api_version": __api_version__}
    if meta.provider:
        replacements.update(
            {
                "provider.name": meta.provider.name,
                "provider.prefix": meta.provider.prefix,
                "provider.description": meta.provider.description,
                "provider.homepage": str(meta.provider.homepage or ""),
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

    for k, v in replacements.items():
        html = html.replace(f"{{{{ {k} }}}}", v)

    endpoints = "\n".join(
        f'<li><a href="{versioned_url}{e}">{versioned_url}{e}</a></li>'
        for e in [*entry_collections.keys(), "info"]
    )
    html = html.replace("{% ENDPOINTS %}", endpoints)

    index_html = (
        f"""<h3>Index base URL:</h3>\n<p><a href="{config.index_base_url}">{config.index_base_url}</a></p>\n"""
        if config.index_base_url
        else ""
    )
    html = html.replace("{% INDEX_BASE_URL %}", index_html)

    resp = HTMLResponse(html)
    _PAGE_CACHE[cache_key] = resp
    return resp


async def landing(request: Request):
    """Show landing page when the base URL is accessed."""
    return render_landing_page(
        request.app.state.config, request.app.state.entry_collections, str(request.url)
    )


router = Router(routes=[Route("/", endpoint=landing)])
