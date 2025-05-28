"""Logging utilities."""

import logging
import os
from typing import Optional


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """Setup logging with appropriate level."""
    level = log_level or os.getenv("WARIFURI_LOG_LEVEL") or "INFO"

    # Validate log level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    return logging.getLogger("warifuri")
