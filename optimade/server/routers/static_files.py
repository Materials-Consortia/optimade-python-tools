"""Serve the contents of `files` entries from the configured static files directory.

When [`static_files`][optimade.server.config.ServerConfig.static_files] is enabled,
the contents of each `files` entry can be downloaded by its ID from
`<base_url><route>/files/<entry_id>`, without having to store the full URL of the
file in the database.

"""

import urllib.parse
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from optimade.exceptions import NotFound
from optimade.server.config import ServerConfig

__all__ = ("create_file_download_router", "file_download_url", "add_file_urls")

FILE_DOWNLOAD_ROUTE_NAME = "download_file_by_id"


def file_download_url(config: ServerConfig, request: Request, entry_id: str) -> str:
    """Return the URL from which the contents of the `files` entry can be downloaded.

    Uses the configured `base_url` if set, otherwise the base URL of the request
    (including any ASGI `root_path`, e.g., when mounted as a sub-application).

    """
    if config.base_url:
        base_url = config.base_url.rstrip("/")
    else:
        # `request.base_url` uses the root path of the top-level app, so build it from
        # this app's `root_path` to account for being mounted as a sub-application
        root_path = request.scope.get("root_path", "").rstrip("/")
        base_url = f"{request.url.scheme}://{request.url.netloc}{root_path}"
    quoted_id = urllib.parse.quote(entry_id, safe="/")
    return f"{base_url}{config.static_files.route}/files/{quoted_id}"


def add_file_urls(
    entries: list[dict[str, Any]] | dict[str, Any] | None,
    request: Request,
    exclude_fields: set[str] | None = None,
) -> None:
    """Fill in the `url` of any `files` entries that do not have one stored in the
    database, pointing to the download route, in-place.

    Only applies when static files are enabled, and does nothing if `url` was
    excluded from the response via `response_fields`.

    Parameters:
        entries: The (mapped) entries of the response, of any entry type.
        request: The current request.
        exclude_fields: The fields excluded from the response.

    """
    config: ServerConfig = request.app.state.config
    if not config.static_files.enabled or config.is_index or not entries:
        return
    if exclude_fields and "url" in exclude_fields:
        return

    if isinstance(entries, dict):
        entries = [entries]

    for entry in entries:
        if not isinstance(entry, dict) or entry.get("type") != "files":
            continue
        attributes = entry.get("attributes")
        if attributes is not None and attributes.get("url") is None:
            attributes["url"] = file_download_url(config, request, entry["id"])


def _resolve_file_path(config: ServerConfig, relative_path: str) -> Path | None:
    """Resolve the path of a file relative to the static files directory,
    returning `None` if it is not a file inside that directory."""
    directory: Path = config.static_files.directory  # type: ignore[assignment]
    try:
        path = (directory / relative_path).resolve()
    except (OSError, ValueError):
        return None
    if not path.is_relative_to(directory) or not path.is_file():
        return None
    return path


def _get_raw_file_entry(request: Request, entry_id: str) -> dict[str, Any] | None:
    """Look up the raw database document of the `files` entry with the given ID,
    including the configured `path_field`."""
    config: ServerConfig = request.app.state.config
    collection = request.app.state.entry_collections["files"]
    mapper = collection.resource_mapper

    escaped_id = entry_id.replace("\\", "\\\\").replace('"', '\\"')
    criteria: dict[str, Any] = {
        "filter": collection.transformer.transform(
            collection.parser.parse(f'id="{escaped_id}"')
        ),
        "projection": {
            mapper.get_backend_field(field): True for field in collection.all_fields
        },
        "limit": 1,
    }
    if config.static_files.path_field:
        criteria["projection"][config.static_files.path_field] = True

    results, _, _ = collection._run_db_query(criteria, single_entry=True)
    return results[0] if results else None


def create_file_download_router(config: ServerConfig) -> APIRouter:
    """Create the router serving the contents of `files` entries by their ID at
    `<route>/files/{entry_id}`."""
    router = APIRouter()

    @router.get(
        f"{config.static_files.route}/files/{{entry_id:path}}",
        name=FILE_DOWNLOAD_ROUTE_NAME,
        tags=["Files"],
        response_class=FileResponse,
        include_in_schema=False,
    )
    def download_file(request: Request, entry_id: str) -> FileResponse:
        """Return the contents of the `files` entry with the given ID."""
        app_config: ServerConfig = request.app.state.config
        raw_entry = _get_raw_file_entry(request, entry_id)
        if raw_entry is None:
            raise NotFound(detail=f"No files entry found with id {entry_id!r}.")

        relative_path = None
        if app_config.static_files.path_field:
            relative_path = raw_entry.get(app_config.static_files.path_field)
        if not relative_path:
            relative_path = entry_id

        path = _resolve_file_path(app_config, str(relative_path))
        if path is None:
            raise NotFound(
                detail=f"The contents of the files entry {entry_id!r} are not available."
            )

        mapper = request.app.state.entry_collections["files"].resource_mapper
        attributes = mapper.map_back(raw_entry)["attributes"]
        return FileResponse(
            path,
            media_type=attributes.get("media_type"),
            filename=attributes.get("name"),
        )

    return router
