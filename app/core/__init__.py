"""Core package — configuration, logging, and shared infrastructure."""

from app.core.config import get_settings, Settings
from app.core.logging import setup_logging

__all__ = ["get_settings", "Settings", "setup_logging"]
