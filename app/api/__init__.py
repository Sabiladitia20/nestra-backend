"""
API Router Aggregator
======================
Combines all route modules under a versioned API prefix.
"""

from fastapi import APIRouter

from app.api.routes import chat, health, prediction
from app.core.config import get_settings

settings = get_settings()


def create_api_router() -> APIRouter:
    """Create and configure the main API router."""
    api_router = APIRouter(prefix=f"/api/{settings.API_VERSION}")

    # Register route modules
    api_router.include_router(health.router)
    api_router.include_router(chat.router)

    # PLTB ML prediction & ranking
    api_router.include_router(prediction.router)
    api_router.include_router(prediction.ranking_router)

    # Future route modules:
    # api_router.include_router(analysis.router)
    # api_router.include_router(rag.router)

    return api_router
