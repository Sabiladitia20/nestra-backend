"""Schemas package — Pydantic models for API validation."""

from app.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    MessageRole,
)
from app.schemas.prediction import (
    LocationInfo,
    PredictRequest,
    PredictResponse,
    PredictionErrorResponse,
    RankingItem,
)

__all__ = [
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "ErrorResponse",
    "HealthResponse",
    "MessageRole",
    "LocationInfo",
    "PredictRequest",
    "PredictResponse",
    "PredictionErrorResponse",
    "RankingItem",
]
