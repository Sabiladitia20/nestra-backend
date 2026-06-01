"""
Health API Router
==================
Health check and system status endpoints.
"""

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.schemas.chat import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the current health status of the API.",
)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=__version__,
        environment=settings.APP_ENV,
    )
