"""
FastAPI Application Factory
=============================
Creates and configures the FastAPI application instance.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app import __app_name__, __version__
from app.api import create_api_router
from app.core.config import get_settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    # --- Startup ---
    setup_logging()
    settings = get_settings()
    logger.info(f"[START] {settings.APP_NAME} v{__version__} starting up...")
    logger.info(f"   Environment: {settings.APP_ENV}")
    logger.info(f"   CORS Origins: {settings.CORS_ORIGINS}")
    logger.info(f"   OpenAI Model: {settings.OPENAI_MODEL}")
    logger.info(f"   PLTB Artifacts: {settings.PLTB_ARTIFACTS_DIR}")
    logger.info(f"   API Docs: http://{settings.HOST}:{settings.PORT}/docs")

    # Pre-initialise PLTB predictor service
    try:
        from app.services.predictor_service import get_predictor_service
        predictor = get_predictor_service()
        _ = predictor.get_locations()  # triggers lazy-load
        logger.info("[PLTB] WindPredictor initialised successfully")
    except Exception as e:
        logger.warning(f"[PLTB] WindPredictor init deferred — {e}")

    yield

    # --- Shutdown ---
    logger.info("[STOP] Application shutting down gracefully...")


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title=__app_name__,
        version=__version__,
        description=(
            "AI/ML Backend untuk Dashboard Nestra — "
            "Platform analisis dan prediksi potensi angin PLTB di Indonesia."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # --- CORS Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Register API Routes ---
    api_router = create_api_router()
    app.include_router(api_router)

    # --- Root endpoint ---
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "app": __app_name__,
            "version": __version__,
            "docs": "/docs",
            "health": f"/api/{settings.API_VERSION}/health",
        }

    return app
