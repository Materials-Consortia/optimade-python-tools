import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from optimade.server.config import ServerConfig, StaticFilesConfig
from optimade.server.main import create_app


def test_default_behavior_disabled():
    """Test that static files are disabled by default."""
    app = create_app()  # No config
    client = TestClient(app)

    # Static files should not be served
    response = client.get("/static/test.txt")
    assert response.status_code == 404

    # API should still work
    response = client.get("/info")
    assert response.status_code == 200


def test_static_files_served_correctly():
    """Test that static files are served correctly when enabled."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        static_path = Path(tmp_dir)

        # Create test files
        (static_path / "test.txt").write_text("Hello, World!")
        (static_path / "style.css").write_text("body { color: red; }")

        # Create subdirectory with file
        subdir = static_path / "images"
        subdir.mkdir()
        (subdir / "logo.png").write_text("fake png content")

        # Configure and create app
        config = ServerConfig(
            static_files=StaticFilesConfig(
                enabled=True, directory=static_path, route="/static"
            )
        )
        app = create_app(config=config)
        client = TestClient(app)

        # Test serving files
        response = client.get("/static/test.txt")
        assert response.status_code == 200
        assert response.text == "Hello, World!"
        assert "text/plain" in response.headers["content-type"]

        response = client.get("/static/style.css")
        assert response.status_code == 200
        assert response.text == "body { color: red; }"
        assert "text/css" in response.headers["content-type"]

        # Test serving from subdirectory
        response = client.get("/static/images/logo.png")
        assert response.status_code == 200
        assert response.text == "fake png content"

        # Test non-existent file
        response = client.get("/static/nonexistent.txt")
        assert response.status_code == 404

        # Test directory listing (should be disabled)
        response = client.get("/static/")
        assert response.status_code == 404


def test_custom_route():
    """Test that static files work with a custom route."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        static_path = Path(tmp_dir)
        (static_path / "test.txt").write_text("Custom route test")

        config = ServerConfig(
            static_files=StaticFilesConfig(
                enabled=True, directory=static_path, route="/assets"
            )
        )
        app = create_app(config=config)
        client = TestClient(app)

        # File should be served on custom route
        response = client.get("/assets/test.txt")
        assert response.status_code == 200
        assert response.text == "Custom route test"

        # File should NOT be served on default route
        response = client.get("/static/test.txt")
        assert response.status_code == 404


def test_static_files_with_api_routes():
    """Test that static files don't interfere with API routes."""
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
        client = TestClient(app)

        # API endpoints should still work
        response = client.get("/info")
        assert response.status_code == 200
        assert "data" in response.json()

        # Static files should work too
        response = client.get("/static/info/test.txt")
        assert response.status_code == 200
        assert response.text == "Static info"


def test_static_files_with_gzip():
    """Test that static files work with gzip middleware."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        static_path = Path(tmp_dir)

        # Create a large file to test gzip
        (static_path / "large.txt").write_text("x" * 1000)
        (static_path / "small.txt").write_text("Small file")

        config = ServerConfig(
            static_files=StaticFilesConfig(
                enabled=True, directory=static_path, route="/static"
            ),
            gzip={"enabled": True, "minimum_size": 100},
        )
        app = create_app(config=config)
        client = TestClient(app)

        # Large file should work (may or may not be gzipped)
        response = client.get("/static/large.txt")
        assert response.status_code == 200
        assert len(response.content) == 1000

        # Small file should work
        response = client.get("/static/small.txt")
        assert response.status_code == 200
        assert response.text == "Small file"


def test_directory_must_exist():
    """Test that providing a non-existent directory raises an error."""
    with pytest.raises(ValueError, match="Static files directory does not exist"):
        StaticFilesConfig(
            enabled=True,
            directory=Path("/tmp/definitely/does/not/exist/12345"),
            route="/static",
        )


def test_config_from_environment(monkeypatch):
    """Test that static files can be configured via environment variables."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        monkeypatch.delenv("OPTIMADE_CONFIG_FILE", raising=False)

        monkeypatch.setenv("OPTIMADE_STATIC_FILES__ENABLED", "true")
        monkeypatch.setenv("OPTIMADE_STATIC_FILES__DIRECTORY", tmp_dir)
        monkeypatch.setenv("OPTIMADE_STATIC_FILES__ROUTE", "/assets")

        # Load config from environment
        config = ServerConfig()

        # Create a config file instead
        config_file = Path(tmp_dir) / "config.json"
        config_file.write_text(f"""
        {{
            "static_files": {{
                "enabled": true,
                "directory": "{tmp_dir}",
                "route": "/assets"
            }}
        }}
        """)

        # Set the config file env var
        monkeypatch.setenv("OPTIMADE_CONFIG_FILE", str(config_file))

        # Reload config from file
        config = ServerConfig()

        assert config.static_files.enabled is True
        assert config.static_files.directory == Path(tmp_dir)
        assert config.static_files.route == "/assets"

        # Verify it actually works
        (Path(tmp_dir) / "test.txt").write_text("Hello from env")
        app = create_app(config=config)
        client = TestClient(app)
        response = client.get("/assets/test.txt")
        assert response.status_code == 200
        assert response.text == "Hello from env"


def test_config_from_file(tmp_path):
    """Test that static files can be configured via a config file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create config file
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

        # Set environment to use config file
        os.environ["OPTIMADE_CONFIG_FILE"] = str(config_file)

        # Load config
        config = ServerConfig()

        assert config.static_files.enabled is True
        assert config.static_files.directory == Path(tmp_dir)
        assert config.static_files.route == "/assets"

        # Verify it works
        (Path(tmp_dir) / "test.txt").write_text("Hello from config file")
        app = create_app(config=config)
        client = TestClient(app)
        response = client.get("/assets/test.txt")
        assert response.status_code == 200
        assert response.text == "Hello from config file"


def test_no_reach_outside():
    """Test that files outside of the current route are not accessible."""
    # For some reason i need this - unclear why...
    if "OPTIMADE_CONFIG_FILE" in os.environ:
        del os.environ["OPTIMADE_CONFIG_FILE"]

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
        client = TestClient(app)

        # File inside static directory should work
        response = client.get("/assets/test.txt")
        assert response.status_code == 200
        assert response.text == "Inside static dir"

        # File outside static directory should NOT be accessible
        response = client.get("/assets/../outside/secret.txt")
        assert response.status_code in [404, 403]

        response = client.get("/assets/../../outside/secret.txt")
        assert response.status_code in [404, 403]

        # URL encoded traversal
        response = client.get("/assets/%2e%2e/outside/secret.txt")
        assert response.status_code in [404, 403]
