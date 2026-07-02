import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from optimade.server.config import ServerConfig, StaticFilesConfig
from optimade.server.main import create_app


class TestStaticFilesDefault:
    """Tests for default static files behavior (disabled)."""

    def test_default_behavior_disabled(self):
        """Test that static files are disabled by default."""
        app = create_app()
        client = TestClient(app)

        response = client.get("/static/test.txt")
        assert response.status_code == 404

        response = client.get("/info")
        assert response.status_code == 200


class TestStaticFilesServing:
    """Tests for serving static files."""

    @pytest.fixture
    def static_app(self):
        """Create an app with static files enabled."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            static_path = Path(tmp_dir)

            # Create test files
            (static_path / "test.txt").write_text("Hello, World!")
            (static_path / "style.css").write_text("body { color: red; }")

            subdir = static_path / "images"
            subdir.mkdir()
            (subdir / "logo.png").write_text("fake png content")

            config = ServerConfig(
                static_files=StaticFilesConfig(
                    enabled=True, directory=static_path, route="/static"
                )
            )
            app = create_app(config=config)
            yield app, static_path

    @pytest.fixture
    def static_client(self, static_app):
        """Create a test client with static files enabled."""
        app, _ = static_app
        return TestClient(app)

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

    def test_serve_file_in_subdirectory(self, static_client):
        """Test serving a file from a subdirectory."""
        response = static_client.get("/static/images/logo.png")
        assert response.status_code == 200
        assert response.text == "fake png content"

    def test_nonexistent_file_returns_404(self, static_client):
        """Test that non-existent file returns 404."""
        response = static_client.get("/static/nonexistent.txt")
        assert response.status_code == 404

    def test_directory_listing_disabled(self, static_client):
        """Test that directory listing is disabled."""
        response = static_client.get("/static/")
        assert response.status_code == 404


class TestStaticFilesCustomRoute:
    """Tests for static files with custom routes."""

    @pytest.fixture
    def custom_route_app(self):
        """Create an app with static files on a custom route."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            static_path = Path(tmp_dir)
            (static_path / "test.txt").write_text("Custom route test")

            config = ServerConfig(
                static_files=StaticFilesConfig(
                    enabled=True, directory=static_path, route="/assets"
                )
            )
            app = create_app(config=config)
            yield app, static_path

    @pytest.fixture
    def custom_route_client(self, custom_route_app):
        """Create a test client with custom route."""
        app, _ = custom_route_app
        return TestClient(app)

    def test_custom_route_works(self, custom_route_client):
        """Test that files are served on the custom route."""
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
    def app_with_static_and_api(self):
        """Create an app with static files and API routes."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            static_path = Path(tmp_dir)

            # Create a file that might conflict with API routes
            (static_path / "info").mkdir()
            (static_path / "info" / "test.txt").write_text("Static info")

            config = ServerConfig(
                static_files=StaticFilesConfig(
                    enabled=True, directory=static_path, route="/static"
                )
            )
            app = create_app(config=config)
            yield app, static_path

    @pytest.fixture
    def client_with_static_and_api(self, app_with_static_and_api):
        """Create a test client."""
        app, _ = app_with_static_and_api
        return TestClient(app)

    def test_api_routes_still_work(self, client_with_static_and_api):
        """Test that API endpoints still work."""
        response = client_with_static_and_api.get("/info")
        assert response.status_code == 200
        assert "data" in response.json()

    def test_static_routes_still_work(self, client_with_static_and_api):
        """Test that static endpoints still work."""
        response = client_with_static_and_api.get("/static/info/test.txt")
        assert response.status_code == 200
        assert response.text == "Static info"


class TestStaticFilesWithGzip:
    """Tests for static files with gzip middleware."""

    @pytest.fixture
    def app_with_gzip(self):
        """Create an app with static files and gzip enabled."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            static_path = Path(tmp_dir)

            (static_path / "large.txt").write_text("x" * 1000)
            (static_path / "small.txt").write_text("Small file")

            config = ServerConfig(
                static_files=StaticFilesConfig(
                    enabled=True, directory=static_path, route="/static"
                ),
                gzip={"enabled": True, "minimum_size": 100},
            )
            app = create_app(config=config)
            yield app, static_path

    @pytest.fixture
    def client_with_gzip(self, app_with_gzip):
        """Create a test client with gzip."""
        app, _ = app_with_gzip
        return TestClient(app)

    def test_large_file_with_gzip(self, client_with_gzip):
        """Test serving a large file with gzip."""
        response = client_with_gzip.get("/static/large.txt")
        assert response.status_code == 200
        assert len(response.content) == 1000

    def test_small_file_with_gzip(self, client_with_gzip):
        """Test serving a small file with gzip."""
        response = client_with_gzip.get("/static/small.txt")
        assert response.status_code == 200
        assert response.text == "Small file"


class TestStaticFilesValidation:
    """Tests for static files validation."""

    def test_directory_must_exist(self):
        """Test that providing a non-existent directory raises an error."""
        with pytest.raises(ValueError, match="Static files directory does not exist"):
            StaticFilesConfig(
                enabled=True,
                directory=Path("/tmp/definitely/does/not/exist/12345"),
                route="/static",
            )


class TestStaticFilesConfiguration:
    """Tests for static files configuration sources."""

    @pytest.fixture(autouse=True)
    def clean_env(self):
        """Clean up environment variables before and after each test."""
        original_config = os.environ.get("OPTIMADE_CONFIG_FILE")
        if "OPTIMADE_CONFIG_FILE" in os.environ:
            del os.environ["OPTIMADE_CONFIG_FILE"]
        yield
        if original_config is not None:
            os.environ["OPTIMADE_CONFIG_FILE"] = original_config

    def test_config_from_file(self, tmp_path, monkeypatch):
        """Test that static files can be configured via a config file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = tmp_path / "config.json"
            config_file.write_text(f"""
            {{
                "static_files": {{
                    "enabled": true,
                    "directory": "{tmp_dir}",
                    "route": "/assets"
                }}
            }}
            """)

            monkeypatch.setenv("OPTIMADE_CONFIG_FILE", str(config_file))

            config = ServerConfig()

            assert config.static_files.enabled is True
            assert config.static_files.directory == Path(tmp_dir)
            assert config.static_files.route == "/assets"

    def test_config_directly_in_python(self):
        """Test that static files can be configured directly in Python."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = ServerConfig(
                static_files=StaticFilesConfig(
                    enabled=True,
                    directory=Path(tmp_dir),
                    route="/custom",
                )
            )

            assert config.static_files.enabled is True
            assert config.static_files.directory == Path(tmp_dir)
            assert config.static_files.route == "/custom"


class TestStaticFilesSecurity:
    """Security tests for static files."""

    @pytest.fixture
    def security_app(self):
        """Create an app with security testing setup."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            static_path = Path(tmp_dir) / "static"
            outside_path = Path(tmp_dir) / "outside"

            static_path.mkdir()
            outside_path.mkdir()

            (static_path / "test.txt").write_text("Inside static dir")
            (outside_path / "secret.txt").write_text("This should not be accessible")

            config = ServerConfig(
                static_files=StaticFilesConfig(
                    enabled=True, directory=static_path, route="/assets"
                )
            )
            app = create_app(config=config)
            yield app, static_path, outside_path

    @pytest.fixture
    def security_client(self, security_app):
        """Create a test client for security tests."""
        app, _, _ = security_app
        return TestClient(app)

    def test_file_inside_mounted_directory_accessible(self, security_client):
        """Test that files inside the mounted directory are accessible."""
        response = security_client.get("/assets/test.txt")
        assert response.status_code == 200
        assert response.text == "Inside static dir"

    def test_file_outside_mounted_directory_not_accessible(self, security_client):
        """Test that files outside the mounted directory are not accessible."""
        response = security_client.get("/assets/../outside/secret.txt")
        assert response.status_code in [404, 403]

    def test_double_dot_traversal_blocked(self, security_client):
        """Test that double dot path traversal is blocked."""
        response = security_client.get("/assets/../../outside/secret.txt")
        assert response.status_code in [404, 403]

    def test_url_encoded_traversal_blocked(self, security_client):
        """Test that URL encoded path traversal is blocked."""
        response = security_client.get("/assets/%2e%2e/outside/secret.txt")
        assert response.status_code in [404, 403]
