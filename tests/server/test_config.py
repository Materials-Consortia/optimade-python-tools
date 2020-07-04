# pylint: disable=protected-access,pointless-statement,relative-beyond-top-level
import json
import os

from pathlib import Path

from optimade.server.config import ServerConfig, CONFIG


def test_env_variable():
    """Set OPTIMADE_DEBUG environment variable and check CONFIG picks up on it correctly"""
    os.environ["OPTIMADE_DEBUG"] = "true"
    CONFIG = ServerConfig()
    assert CONFIG.debug

    os.environ.pop("OPTIMADE_DEBUG", None)
    CONFIG = ServerConfig()
    assert not CONFIG.debug


def test_default_config_path():
    """Make sure the default config path works
    Expected default config path: PATH/TO/USER/HOMEDIR/.optimade.json
    """
    # Reset OPTIMADE_CONFIG_FILE
    original_OPTIMADE_CONFIG_FILE = os.environ.get("OPTIMADE_CONFIG_FILE", "")
    os.environ.pop("OPTIMADE_CONFIG_FILE")

    with open(
        Path(__file__).parent.parent.joinpath("test_config.json"), "r"
    ) as config_file:
        config = json.load(config_file)

    different_base_url = "http://something_you_will_never_think_of.com"
    config["base_url"] = different_base_url

    # Try-finally to make sure we don't overwrite possible existing `.optimade.json`
    original = Path.home().joinpath(".optimade.json")
    restore = False
    if original.exists():
        restore = True
        with open(original, "rb") as original_file:
            original_file_content = original_file.read()
    try:
        with open(Path.home().joinpath(".optimade.json"), "w") as default_config_file:
            json.dump(config, default_config_file)
        CONFIG = ServerConfig()
        assert CONFIG.base_url == different_base_url, (
            f"\nDumped file content:\n{config}.\n\nLoaded CONFIG:\n{CONFIG}",
        )
    finally:
        if restore:
            with open(original, "wb") as original_file:
                original_file.write(original_file_content)

    # Restore OPTIMADE_CONFIG_FILE
    os.environ["OPTIMADE_CONFIG_FILE"] = original_OPTIMADE_CONFIG_FILE


def test_debug_is_respected_when_off(both_clients):
    """Make sure traceback is toggleable according to debug mode - here OFF

    TODO: This should be moved to a separate test file that tests the exception handlers.
    """
    if CONFIG.debug:
        CONFIG.debug = False

    response = both_clients.get("/non/existent/path")
    assert (
        response.status_code == 404
    ), f"Request should have failed, but didn't: {response.json()}"

    response = response.json()
    assert "data" not in response
    assert "meta" in response

    assert f"_{CONFIG.provider.prefix}_traceback" not in response["meta"]


def test_debug_is_respected_when_on(both_clients):
    """Make sure traceback is toggleable according to debug mode - here ON

    TODO: This should be moved to a separate test file that tests the exception handlers.
    """
    CONFIG.debug = True

    response = both_clients.get("/non/existent/path")
    assert (
        response.status_code == 404
    ), f"Request should have failed, but didn't: {response.json()}"

    response = response.json()
    assert "data" not in response
    assert "meta" in response

    assert f"_{CONFIG.provider.prefix}_traceback" in response["meta"]
