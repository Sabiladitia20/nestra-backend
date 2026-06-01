"""
Logging Configuration
=====================
Structured logging with Loguru for observability.
Supports both console and file output.
"""

import sys
from pathlib import Path

from loguru import logger

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure application-wide logging with Loguru."""
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Console handler — colorful, human-readable
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File handler — JSON structured for production analysis
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_path),
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} — {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        serialize=settings.is_production,
    )

    logger.info(f"Logging initialized — level={settings.LOG_LEVEL}, env={settings.APP_ENV}")
