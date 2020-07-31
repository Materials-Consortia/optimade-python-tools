"""Logging to both file and terminal"""
import logging
import os
from pathlib import Path
import sys

from uvicorn.logging import DefaultFormatter


# Instantiate LOGGER
LOGGER = logging.getLogger("optimade")
LOGGER.setLevel(logging.DEBUG)

# Handler
CONSOLE_HANDLER = logging.StreamHandler(sys.stdout)
try:
    from optimade.server.config import CONFIG

    CONSOLE_HANDLER.setLevel(CONFIG.log_level.value.upper())
except ImportError:
    CONSOLE_HANDLER.setLevel(os.getenv("OPTIMADE_LOG_LEVEL", "INFO").upper())

# Formatter
CONSOLE_FORMATTER = DefaultFormatter("%(levelprefix)s [%(name)s] %(message)s")
CONSOLE_HANDLER.setFormatter(CONSOLE_FORMATTER)

# Add handler to LOGGER
LOGGER.addHandler(CONSOLE_HANDLER)

# Save a file with all messages (DEBUG level)
try:
    from optimade.server.config import CONFIG

    LOGS_DIR = CONFIG.log_dir
except ImportError:
    LOGS_DIR = Path(os.getenv("OPTIMADE_LOG_DIR", "/var/log/optimade/")).resolve()
try:
    LOGS_DIR.mkdir(exist_ok=True)
except PermissionError:
    import warnings
    from optimade.server.warnings import LogsNotSaved

    warnings.warn(LogsNotSaved())
else:
    # Handlers
    FILE_HANDLER = logging.handlers.RotatingFileHandler(
        LOGS_DIR.joinpath("optimade.log"), maxBytes=1000000, backupCount=5
    )
    FILE_HANDLER.setLevel(logging.DEBUG)

    # Formatter
    FILE_FORMATTER = logging.Formatter(
        "[%(levelname)-8s %(asctime)s %(filename)s:%(lineno)d][%(name)s] %(message)s",
        "%d-%m-%Y %H:%M:%S",
    )
    FILE_HANDLER.setFormatter(FILE_FORMATTER)

    # Add handler to LOGGER
    LOGGER.addHandler(FILE_HANDLER)
