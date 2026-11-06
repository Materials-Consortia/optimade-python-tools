import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from optimade.server.config import ServerConfig, StaticFilesConfig
from optimade.server.create_app import INDEX_ENDPOINTS, MAIN_ENDPOINTS
from optimade.server.main import create_app

# A minimal valid PNG header followed by bytes that are invalid UTF-8
PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + bytes(range(256))


def make_static_app(directory: Path, route: str = "/static", **config_kwargs):
    config = ServerConfig(
        static_files=StaticFilesConfig(enabled=True, directory=directory, route=route),
        **config_kwargs,
    )
    return create_app(config=config)


def raw_asgi_get(app, path: str) -> tuple[int, bytes]:
    """Send a GET request directly to the ASGI app with an un-normalised path.

    HTTP clients such as httpx (used by `TestClient`) normalise `..` segments
    before sending the request, so they cannot be used to test path traversal.

    """
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": b"",
        "headers": [(b"host", b"testserver")],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    status = 0
    body = b""
    request_sent = False

    async def run():
        response_complete = asyncio.Event()

        async def receive():
            nonlocal request_sent
            if not request_sent:
                request_sent = True
                return {"type": "http.request", "body": b"", "more_body": False}
            await response_complete.wait()
            return {"type": "http.disconnect"}

        async def send(message):
            nonlocal status, body
            if message["type"] == "http.response.start":
                status = message["status"]
            elif message["type"] == "http.response.body":
                body += message.get("body", b"")
                if not message.get("more_body", False):
                    response_complete.set()

        await app(scope, receive, send)

    asyncio.run(run())
    return status, body


class TestStaticFilesDefault:
    """Tests for default static files behavior (disabled)."""

    def test_default_behavior_disabled(self):
        """Test that static files are disabled by default."""
        client = TestClient(create_app())

        response = client.get("/static/test.txt")
        assert response.status_code == 404

        response = client.get("/info")
        assert response.status_code == 200


class TestStaticFilesServing:
    """Tests for serving static files."""

    @pytest.fixture
    def static_client(self, tmp_path):
        """Create a test client with static files enabled."""
        (tmp_path / "test.txt").write_text("Hello, World!")
        (tmp_path / "style.css").write_text("body { color: red; }")
        (tmp_path / "data.json").write_text('{"a": 1}')
        subdir = tmp_path / "images"
        subdir.mkdir()
        (subdir / "logo.png").write_bytes(PNG_BYTES)
        return TestClient(make_static_app(tmp_path))

    def test_serve_text_file(self, static_client):
        """Test serving a text file."""
        response = static_client.get("/static/test.txt")
        assert response.status_code == 200
        assert response.text == "Hello, World!"
        assert "text/plain" in response.headers["content-type"]

    def test_serve_css_file(self, static_client):
        """Test serving a CSS file."""
        response = static_client.get("/static/style.css")
        assert response.status_code == 200
        assert response.text == "body { color: red; }"
        assert "text/css" in response.headers["content-type"]

    def test_serve_json_file(self, static_client):
        """Test that JSON files are served unchanged."""
        response = static_client.get("/static/data.json")
        assert response.status_code == 200
        assert response.json() == {"a": 1}

    def test_serve_binary_file_in_subdirectory(self, static_client):
        """Test serving a binary (non-UTF-8) file from a subdirectory."""
        response = static_client.get("/static/images/logo.png")
        assert response.status_code == 200
        assert response.content == PNG_BYTES
        assert response.headers["content-type"] == "image/png"
        assert response.headers["content-length"] == str(len(PNG_BYTES))

    def test_nonexistent_file_returns_404(self, static_client):
        """Test that non-existent file returns 404."""
        response = static_client.get("/static/nonexistent.txt")
        assert response.status_code == 404

    def test_directory_listing_disabled(self, static_client):
        """Test that directory listing is disabled."""
        response = static_client.get("/static/")
        assert response.status_code == 404

    def test_unknown_api_path_still_returns_optimade_error(self, static_client):
        """Test that the static mount does not swallow unknown API paths."""
        response = static_client.get("/not_an_endpoint")
        assert response.status_code == 404
        assert "errors" in response.json()


class TestStaticFilesCustomRoute:
    """Tests for static files with custom routes."""

    @pytest.fixture
    def custom_route_client(self, tmp_path):
        """Create a test client with custom route."""
        (tmp_path / "test.txt").write_text("Custom route test")
        return TestClient(make_static_app(tmp_path, route="/assets/"))

    def test_custom_route_works(self, custom_route_client):
        """Test that files are served on the custom (normalised) route."""
        response = custom_route_client.get("/assets/test.txt")
        assert response.status_code == 200
        assert response.text == "Custom route test"

    def test_default_route_not_used(self, custom_route_client):
        """Test that files are not served on the default route."""
        response = custom_route_client.get("/static/test.txt")
        assert response.status_code == 404


class TestStaticFilesWithAPI:
    """Tests that static files don't interfere with API routes."""

    @pytest.fixture
    def client_with_static_and_api(self, tmp_path):
        """Create a test client whose static directory mirrors an API path."""
        (tmp_path / "info").mkdir()
        (tmp_path / "info" / "test.txt").write_text("Static info")
        return TestClient(make_static_app(tmp_path))

    def test_api_routes_still_work(self, client_with_static_and_api):
        """Test that API endpoints still work."""
        for path in ("/info", "/v1/info", "/structures", "/versions"):
            response = client_with_static_and_api.get(path)
            assert response.status_code == 200, path

    def test_static_routes_still_work(self, client_with_static_and_api):
        """Test that static endpoints still work."""
        response = client_with_static_and_api.get("/static/info/test.txt")
        assert response.status_code == 200
        assert response.text == "Static info"

    def test_api_warnings_still_added(self, client_with_static_and_api):
        """Test that the warnings middleware still adds warnings to API responses."""
        response = client_with_static_and_api.get(
            "/structures", params={"_unknown_param": "1"}
        )
        assert response.status_code == 200
        warnings = response.json()["meta"]["warnings"]
        assert warnings[0]["title"] == "UnknownProviderQueryParameter"


class TestStaticFilesWithGzip:
    """Tests for static files with gzip middleware."""

    @pytest.fixture
    def client_with_gzip(self, tmp_path):
        """Create a test client with gzip."""
        (tmp_path / "large.txt").write_text("x" * 1000)
        (tmp_path / "small.txt").write_text("Small file")
        (tmp_path / "large.png").write_bytes(PNG_BYTES * 10)
        return TestClient(
            make_static_app(tmp_path, gzip={"enabled": True, "minimum_size": 100})
        )

    def test_large_file_with_gzip(self, client_with_gzip):
        """Test that a large file is gzip-compressed."""
        response = client_with_gzip.get(
            "/static/large.txt", headers={"Accept-Encoding": "gzip"}
        )
        assert response.status_code == 200
        assert response.headers.get("content-encoding") == "gzip"
        assert response.text == "x" * 1000

    def test_large_binary_file_with_gzip(self, client_with_gzip):
        """Test that a large binary file is served intact when gzip is enabled
        (note: PNGs are excluded from compression by Starlette's GZipMiddleware)."""
        response = client_with_gzip.get(
            "/static/large.png", headers={"Accept-Encoding": "gzip"}
        )
        assert response.status_code == 200
        assert response.content == PNG_BYTES * 10

    def test_small_file_with_gzip(self, client_with_gzip):
        """Test serving a small file with gzip enabled."""
        response = client_with_gzip.get(
            "/static/small.txt", headers={"Accept-Encoding": "gzip"}
        )
        assert response.status_code == 200
        assert response.text == "Small file"


class TestStaticFilesValidation:
    """Tests for static files config validation."""

    def test_directory_must_exist(self, tmp_path):
        """Test that providing a non-existent directory raises an error."""
        with pytest.raises(
            ValidationError, match="Static files directory does not exist"
        ):
            StaticFilesConfig(enabled=True, directory=tmp_path / "does_not_exist")

    def test_directory_must_be_a_directory(self, tmp_path):
        """Test that providing a file instead of a directory raises an error."""
        (tmp_path / "file.txt").write_text("not a directory")
        with pytest.raises(ValidationError, match="is not a directory"):
            StaticFilesConfig(enabled=True, directory=tmp_path / "file.txt")

    def test_directory_required_when_enabled(self):
        """Test that enabling static files without a directory raises an error."""
        with pytest.raises(ValidationError, match="must be provided"):
            StaticFilesConfig(enabled=True)

    def test_directory_not_checked_when_disabled(self, tmp_path):
        """Test that a missing directory is ignored when static files are disabled."""
        missing = tmp_path / "does_not_exist"
        config = StaticFilesConfig(enabled=False, directory=missing)
        assert config.directory == missing
        ServerConfig(static_files={"enabled": False, "directory": str(missing)})

    def test_relative_directory_resolved(self, tmp_path, monkeypatch):
        """Test that a relative directory is resolved to an absolute path."""
        (tmp_path / "static").mkdir()
        monkeypatch.chdir(tmp_path)
        config = StaticFilesConfig(enabled=True, directory=Path("static"))
        assert config.directory == (tmp_path / "static").resolve()
        assert config.directory.is_absolute()

    @pytest.mark.parametrize("route", ["static", "", "assets/"])
    def test_route_must_start_with_slash(self, route):
        """Test that routes without a leading slash are rejected."""
        with pytest.raises(ValidationError, match="must start with '/'"):
            StaticFilesConfig(route=route)

    @pytest.mark.parametrize("route", ["/", "//"])
    def test_root_route_rejected(self, route):
        """Test that the root route is rejected, as it would shadow the API."""
        with pytest.raises(ValidationError, match="cannot be '/'"):
            StaticFilesConfig(route=route)

    @pytest.mark.parametrize(
        "route",
        [
            "/info",
            "/links",
            "/references",
            "/structures/",
            "/files",
            "/versions",
            "/extensions/static",
            "/v1",
            "/v1.2",
            "/v1.2.3/static",
        ],
    )
    def test_route_clashing_with_api_rejected(self, route):
        """Test that routes clashing with OPTIMADE API paths are rejected."""
        with pytest.raises(ValidationError, match="clashes with the OPTIMADE API"):
            StaticFilesConfig(route=route)

    @pytest.mark.parametrize(
        "route, expected",
        [
            ("/static", "/static"),
            ("/static/", "/static"),
            ("/assets/v1", "/assets/v1"),
            ("/information", "/information"),
        ],
    )
    def test_valid_routes(self, route, expected):
        """Test that valid routes are accepted and normalised."""
        assert StaticFilesConfig(route=route).route == expected


class TestStaticFilesConfiguration:
    """Tests for static files configuration sources."""

    def test_config_from_file(self, tmp_path, monkeypatch):
        """Test that static files can be configured via a config file."""
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        config_file = tmp_path / "config.json"
        config_file.write_text(
            f"""
            {{
                "static_files": {{
                    "enabled": true,
                    "directory": "{static_dir}",
                    "route": "/assets"
                }}
            }}
            """
        )
        monkeypatch.setenv("OPTIMADE_CONFIG_FILE", str(config_file))

        config = ServerConfig()

        assert config.static_files.enabled is True
        assert config.static_files.directory == static_dir.resolve()
        assert config.static_files.route == "/assets"

    def test_config_directly_in_python(self, tmp_path):
        """Test that static files can be configured directly in Python."""
        config = ServerConfig(
            static_files=StaticFilesConfig(
                enabled=True, directory=tmp_path, route="/custom"
            )
        )

        assert config.static_files.enabled is True
        assert config.static_files.directory == tmp_path.resolve()
        assert config.static_files.route == "/custom"


class TestStaticFilesSecurity:
    """Security tests for static files."""

    @pytest.fixture
    def security_app(self, tmp_path):
        """Create an app with a secret file next to the static directory."""
        static_path = tmp_path / "static"
        outside_path = tmp_path / "outside"
        static_path.mkdir()
        outside_path.mkdir()
        (static_path / "test.txt").write_text("Inside static dir")
        (outside_path / "secret.txt").write_text("This should not be accessible")
        return make_static_app(static_path, route="/assets")

    def test_file_inside_mounted_directory_accessible(self, security_app):
        """Test that files inside the mounted directory are accessible, both via a
        client and via the raw ASGI helper used for the traversal tests below."""
        response = TestClient(security_app).get("/assets/test.txt")
        assert response.status_code == 200
        assert response.text == "Inside static dir"

        status, body = raw_asgi_get(security_app, "/assets/test.txt")
        assert status == 200
        assert body == b"Inside static dir"

    @pytest.mark.parametrize(
        "path",
        [
            "/assets/../outside/secret.txt",
            "/assets/../../outside/secret.txt",
            "/assets/sub/../../outside/secret.txt",
        ],
    )
    def test_path_traversal_blocked(self, security_app, path):
        """Test that `..` path traversal is blocked by the static files mount.

        The requests are sent with the raw (un-normalised) path so that they
        actually reach the static files mount.

        """
        status, body = raw_asgi_get(security_app, path)
        assert status == 404
        assert b"should not be accessible" not in body

    def test_url_encoded_traversal_blocked(self, security_app):
        """Test that URL encoded path traversal is blocked."""
        response = TestClient(security_app).get("/assets/%2e%2e/outside/secret.txt")
        assert response.status_code == 404
        assert "should not be accessible" not in response.text


def test_create_app_does_not_mutate_endpoint_lists():
    """Test that `create_app` does not modify the module-level endpoint lists."""
    main_before = list(MAIN_ENDPOINTS)
    index_before = list(INDEX_ENDPOINTS)

    create_app()
    create_app()
    create_app(index=True)

    assert MAIN_ENDPOINTS == main_before
    assert INDEX_ENDPOINTS == index_before


class TestFileDownloadById:
    """Tests for serving the contents of `files` entries by their ID."""

    @pytest.fixture
    def files_app(self, tmp_path):
        """Create an app with a fresh `files` collection whose entries refer to
        files in the static directory by ID or via `path_field`."""
        import uuid
        from datetime import datetime, timezone

        static_path = tmp_path / "static"
        (static_path / "cifs").mkdir(parents=True)
        (static_path / "dir" / "with").mkdir(parents=True)
        (tmp_path / "outside").mkdir()

        (static_path / "file_by_id").write_text("Found by ID")
        (static_path / "cifs" / "1.cif").write_text("data_1")
        (static_path / "dir" / "with" / "slash").write_bytes(PNG_BYTES)
        (tmp_path / "outside" / "secret.txt").write_text(
            "This should not be accessible"
        )

        config = ServerConfig(
            static_files=StaticFilesConfig(
                enabled=True, directory=static_path, path_field="local_path"
            ),
            files_collection=f"files_{uuid.uuid4().hex}",
            # derive the base URL from the request, unless set explicitly in a test
            base_url=None,
        )
        app = create_app(config=config)

        now = datetime.now(timezone.utc)

        def entry(id_, **kwargs):
            return {"id": id_, "name": id_, "last_modified": now, **kwargs}

        app.state.entry_collections["files"].insert(
            [
                entry("file_by_id", media_type="text/plain", name="by_id.txt"),
                entry(
                    "file_by_path",
                    local_path="cifs/1.cif",
                    media_type="chemical/x-cif",
                    name="1.cif",
                ),
                entry("dir/with/slash"),
                entry("file_external", url="https://example.org/external.cif"),
                entry("file_missing", local_path="does_not_exist.txt"),
                entry("file_escape", local_path="../outside/secret.txt"),
                entry("file_absolute", local_path=str(tmp_path / "outside/secret.txt")),
            ]
        )
        return app

    @pytest.fixture
    def files_client(self, files_app):
        return TestClient(files_app)

    def test_download_by_id(self, files_client):
        """Test that a file named after the entry ID is served."""
        response = files_client.get("/static/files/file_by_id")
        assert response.status_code == 200
        assert response.text == "Found by ID"
        assert response.headers["content-type"].startswith("text/plain")
        assert "by_id.txt" in response.headers["content-disposition"]

    def test_download_by_path_field(self, files_client):
        """Test that a file is found via the configured `path_field`."""
        response = files_client.get("/static/files/file_by_path")
        assert response.status_code == 200
        assert response.text == "data_1"
        assert response.headers["content-type"] == "chemical/x-cif"
        assert "1.cif" in response.headers["content-disposition"]

    def test_download_id_with_slashes(self, files_client):
        """Test that IDs containing slashes are supported, and binary files are intact."""
        response = files_client.get("/static/files/dir/with/slash")
        assert response.status_code == 200
        assert response.content == PNG_BYTES

    @pytest.mark.parametrize(
        "entry_id",
        [
            "does_not_exist",
            "file_missing",
            "file_external",
            "file_escape",
            "file_absolute",
        ],
    )
    def test_download_not_available(self, files_client, entry_id):
        """Test that unknown entries, missing files and paths outside of the
        static directory all return a 404 OPTIMADE error."""
        response = files_client.get(f"/static/files/{entry_id}")
        assert response.status_code == 404
        assert "errors" in response.json()
        assert "should not be accessible" not in response.text

    def test_static_files_still_served_by_path(self, files_client):
        """Test that files are still served by path outside of `<route>/files/`."""
        response = files_client.get("/static/cifs/1.cif")
        assert response.status_code == 200
        assert response.text == "data_1"

    def test_url_filled_in_for_entries_without_url(self, files_client):
        """Test that the `url` of entries without one points to the download route,
        and that stored URLs are left untouched."""
        response = files_client.get("/files")
        assert response.status_code == 200
        urls = {e["id"]: e["attributes"]["url"] for e in response.json()["data"]}
        assert urls["file_by_id"] == "http://testserver/static/files/file_by_id"
        assert urls["file_by_path"] == "http://testserver/static/files/file_by_path"
        assert urls["dir/with/slash"] == "http://testserver/static/files/dir/with/slash"
        assert urls["file_external"] == "https://example.org/external.cif"

        # and the generated URL can be followed
        assert files_client.get(urls["file_by_path"]).text == "data_1"

    def test_url_filled_in_single_entry(self, files_client):
        """Test that the `url` is filled in for single-entry responses, including
        when explicitly requested via `response_fields`."""
        response = files_client.get("/files/file_by_id")
        assert response.status_code == 200
        url = response.json()["data"]["attributes"]["url"]
        assert url == "http://testserver/static/files/file_by_id"

        response = files_client.get(
            "/v1/files/file_by_id", params={"response_fields": "url"}
        )
        assert response.status_code == 200
        assert response.json()["data"]["attributes"] == {"url": url}

    def test_url_not_added_when_excluded(self, files_client):
        """Test that `url` is not added when excluded via `response_fields`."""
        response = files_client.get(
            "/files/file_by_id", params={"response_fields": "name"}
        )
        assert response.status_code == 200
        assert "url" not in response.json()["data"]["attributes"]

    def test_url_uses_configured_base_url(self, files_app):
        """Test that the configured `base_url` is used for the generated `url`."""
        files_app.state.config.base_url = "https://example.org/optimade/"
        response = TestClient(files_app).get("/files/file_by_id")
        assert response.status_code == 200
        assert (
            response.json()["data"]["attributes"]["url"]
            == "https://example.org/optimade/static/files/file_by_id"
        )

    def test_url_uses_root_path_when_mounted(self, files_app):
        """Test that the generated `url` includes the path at which the app is mounted."""
        from fastapi import FastAPI

        parent = FastAPI()
        parent.mount("/sub", files_app)
        client = TestClient(parent)

        url = client.get("/sub/files/file_by_id").json()["data"]["attributes"]["url"]
        assert url == "http://testserver/sub/static/files/file_by_id"
        response = client.get(url)
        assert response.status_code == 200
        assert response.text == "Found by ID"

    def test_no_download_route_when_disabled(self):
        """Test that the download route is not added when static files are disabled."""
        response = TestClient(create_app()).get("/static/files/file_1")
        assert response.status_code == 404
