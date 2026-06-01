"""
Prediction Schemas
===================
Pydantic models for wind speed prediction request/response validation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Request ─────────────────────────────────────────────────────────────────


class PredictRequest(BaseModel):
    """Incoming prediction request from the frontend."""

    location: str = Field(
        ...,
        min_length=1,
        description="Location ID, e.g. 'pandeglang', 'baron', 'bawean'",
        json_schema_extra={"examples": ["pandeglang"]},
    )
    recent_ws10m: List[float] = Field(
        ...,
        min_length=1,
        description=(
            "Recent wind speed measurements at 10 m (m/s), "
            "chronological order — last element = most recent hour. "
            "Minimum 24 data points required."
        ),
    )
    target_time: str = Field(
        ...,
        description="ISO 8601 datetime for the prediction target, e.g. '2026-01-01T08:00:00'",
        json_schema_extra={"examples": ["2026-01-01T08:00:00"]},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "location": "pandeglang",
                    "recent_ws10m": [
                        4.5, 4.3, 4.1, 3.9, 3.7, 3.5, 3.8, 4.0,
                        4.2, 4.4, 4.6, 4.8, 5.0, 5.2, 5.1, 4.9,
                        4.7, 4.5, 4.3, 4.1, 4.0, 3.9, 4.1, 4.3,
                    ],
                    "target_time": "2026-01-01T08:00:00",
                }
            ]
        }
    }


# ── Response ────────────────────────────────────────────────────────────────


class PredictResponse(BaseModel):
    """Prediction result returned to the frontend."""

    location: str
    target_time: str
    predicted_ws10m: float = Field(
        ..., description="Predicted wind speed at 10 m in m/s"
    )
    unit: str = "m/s"
    scenario: str = Field(
        ..., description="Feature scenario used by the model (e.g. S4, S7)"
    )
    model_confidence_r2: float = Field(
        ..., description="R² score on held-out test set"
    )
    model_test_mae: float = Field(
        ..., description="MAE on held-out test set (m/s)"
    )


# ── Ranking ─────────────────────────────────────────────────────────────────


class RankingMetrics(BaseModel):
    """Ranking metrics for a single site."""

    meanWindSpeed: float
    windPowerDensity: float
    operationalHoursPct: float
    windStabilityCV: float
    modelR2: float


class RankingCoordinates(BaseModel):
    """Geographical coordinates."""

    lat: float
    lng: float


class RankingItem(BaseModel):
    """Single site in the ranking list."""

    id: str
    name: str
    rank: int
    coordinates: RankingCoordinates
    feasibilityScore: float
    status: str
    category: str
    bestScenario: str
    metrics: RankingMetrics


# ── Locations ───────────────────────────────────────────────────────────────


class LocationMetrics(BaseModel):
    """Model performance metrics for a location."""

    mae: Optional[float] = None
    rmse: Optional[float] = None
    mape: Optional[float] = None
    r2: Optional[float] = None


class LocationInfo(BaseModel):
    """Available location for prediction."""

    id: str
    name: str
    scenario: str
    status: str
    metrics: LocationMetrics = Field(default_factory=LocationMetrics)
    feature_count: int = 0


# ── Error ───────────────────────────────────────────────────────────────────


class PredictionErrorResponse(BaseModel):
    """Standardized prediction error response."""

    error: str
    detail: str
    status_code: int
