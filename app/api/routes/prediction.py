"""
Prediction API Router
======================
Endpoints for PLTB wind speed prediction and site ranking.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from app.schemas.prediction import (
    LocationInfo,
    PredictRequest,
    PredictResponse,
    PredictionErrorResponse,
    RankingItem,
)
from app.services.predictor_service import get_predictor_service

router = APIRouter(prefix="/predict", tags=["Prediction"])


# ── POST /predict ───────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=PredictResponse,
    summary="Predict wind speed (1 hour ahead)",
    description=(
        "Prediksi kecepatan angin 1 jam ke depan menggunakan model Random Forest. "
        "Membutuhkan minimal 24 data riwayat WS10M (m/s)."
    ),
    responses={
        200: {"model": PredictResponse, "description": "Prediction result"},
        400: {"model": PredictionErrorResponse, "description": "Invalid input"},
        500: {"model": PredictionErrorResponse, "description": "Server error"},
    },
)
async def predict_wind_speed(request: PredictRequest):
    """
    Main prediction endpoint.

    Accepts location, recent wind speed data, and target datetime.
    Returns predicted wind speed with model confidence metrics.
    """
    logger.info(
        f"Prediction request — location={request.location}, "
        f"data_points={len(request.recent_ws10m)}, "
        f"target={request.target_time}"
    )

    try:
        service = get_predictor_service()
        result = service.predict(
            location=request.location,
            recent_ws10m=request.recent_ws10m,
            target_time=request.target_time,
        )
        return PredictResponse(**result)

    except KeyError as e:
        logger.warning(f"Prediction failed — unknown location: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "unknown_location",
                "detail": str(e),
                "status_code": 400,
            },
        )
    except ValueError as e:
        logger.warning(f"Prediction failed — invalid data: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "invalid_input",
                "detail": str(e),
                "status_code": 400,
            },
        )
    except FileNotFoundError as e:
        logger.error(f"Prediction failed — model not found: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "model_not_found",
                "detail": str(e),
                "status_code": 500,
            },
        )
    except Exception as e:
        logger.error(f"Prediction failed — unexpected error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "prediction_failed",
                "detail": str(e),
                "status_code": 500,
            },
        )


# ── GET /predict/locations ──────────────────────────────────────────────────


@router.get(
    "/locations",
    response_model=List[LocationInfo],
    summary="List available prediction locations",
    description="Mengembalikan daftar lokasi PLTB yang tersedia untuk prediksi.",
)
async def list_locations():
    """Return all available locations from the model registry."""
    try:
        service = get_predictor_service()
        locations = service.get_locations()
        logger.info(f"Locations endpoint — returning {len(locations)} locations")
        return [LocationInfo(**loc) for loc in locations]
    except Exception as e:
        logger.error(f"Failed to list locations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ── GET /ranking ────────────────────────────────────────────────────────────


ranking_router = APIRouter(prefix="/ranking", tags=["Ranking"])


@ranking_router.get(
    "",
    response_model=List[RankingItem],
    summary="Get site feasibility ranking",
    description=(
        "Mengembalikan ranking kelayakan lokasi PLTB berdasarkan skor komposit. "
        "Data dari ranking.json."
    ),
)
async def get_ranking():
    """Return site ranking from ranking.json."""
    try:
        service = get_predictor_service()
        ranking = service.get_ranking()
        logger.info(f"Ranking endpoint — returning {len(ranking)} sites")
        return ranking
    except FileNotFoundError as e:
        logger.error(f"Ranking file not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to get ranking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ── GET /predict/metrics ────────────────────────────────────────────────────


@router.get(
    "/metrics",
    response_model=List[Dict[str, Any]],
    summary="Get model performance metrics",
    description="Mengembalikan metrik performa model dari final_metrics.csv.",
)
async def get_metrics():
    """Return final metrics for all locations."""
    try:
        service = get_predictor_service()
        metrics = service.get_metrics()
        logger.info(f"Metrics endpoint — returning {len(metrics)} rows")
        return metrics
    except FileNotFoundError as e:
        logger.error(f"Metrics file not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
