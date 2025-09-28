"""Logging factory to create instance-specific loggers for mounted subapps"""

import logging
import logging.handlers
import os
import sys
from contextvars import ContextVar
from pathlib import Path

from optimade.server.config import ServerConfig

# Context variable for keeping track of the app-specific tag for logging
_current_log_tag: ContextVar[str | None] = ContextVar("current_log_tag", default=None)


def set_logging_context(tag: str | None):
    """Set the current API tag for context-based logging"""
    _current_log_tag.set(tag)


def get_logger() -> logging.Logger:
    """
    Get logger for current context.
    """
    tag = _current_log_tag.get()
    logger_name = "optimade" + (f".{tag}" if tag else "")
    return logging.getLogger(logger_name)


def create_logger(
    tag: str | None = None, config: ServerConfig | None = None
) -> logging.Logger:
    """
    Create a logger instance for a specific app. The purpose of this function
    is to have different loggers for different subapps (if needed).

    Args:
        tag: String added to the each logging line idenfiting this logger
        config: ServerConfig instance, will create the default one if not provided

    Returns:
        Configured logger instance
    """
    config = config or ServerConfig()

    logger_name = "optimade" + (f".{tag}" if tag else "")
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    # Console handler only on parent (.tag will propagate to parent anyway)
    if tag is None:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG if config.debug else config.log_level.value.upper())
        try:
            from uvicorn.logging import DefaultFormatter

            ch.setFormatter(DefaultFormatter("%(levelprefix)s [%(name)s] %(message)s"))
        except ImportError:
            pass
        logger.addHandler(ch)

    logs_dir = config.log_dir
    if logs_dir is None:
        logs_dir = Path(os.getenv("OPTIMADE_LOG_DIR", "/var/log/optimade/")).resolve()
    try:
        logs_dir.mkdir(exist_ok=True, parents=True)
        log_filename = f"optimade_{tag}.log" if tag else "optimade.log"
        fh = logging.handlers.RotatingFileHandler(
            logs_dir / log_filename, maxBytes=1_000_000, backupCount=5
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(
            logging.Formatter(
                "[%(levelname)-8s %(asctime)s %(filename)s:%(lineno)d][%(name)s] %(message)s",
                "%d-%m-%Y %H:%M:%S",
            )
        )
        logger.addHandler(fh)
    except OSError:
        logger.warning(
            "Log files are not saved (%s). Set OPTIMADE_LOG_DIR or fix permissions for %s.",
            tag,
            logs_dir,
        )

    return logger


# Create the global logger without a tag.
LOGGER = create_logger()
