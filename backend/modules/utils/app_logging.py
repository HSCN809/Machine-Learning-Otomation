"""Central logging configuration for the FastAPI application."""

from __future__ import annotations

import logging
import os


def configure_logging() -> None:
    """Configure process-wide logging with Rich when it is available."""

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    try:
        from rich.logging import RichHandler

        handler: logging.Handler = RichHandler(
            rich_tracebacks=True,
            show_path=False,
            markup=False,
        )
        log_format = "%(message)s"
    except ImportError:
        handler = logging.StreamHandler()
        log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt="[%X]",
        handlers=[handler],
        force=True,
    )
    logging.captureWarnings(True)

    logging.getLogger("uvicorn.access").disabled = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger after central configuration is applied."""

    return logging.getLogger(name)
