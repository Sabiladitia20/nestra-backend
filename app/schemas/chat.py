"""
Chat Schemas
=============
Pydantic models for chat request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Chat message role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Single chat message in a conversation."""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Incoming chat request from the frontend."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="User message to the AI assistant",
    )
    conversation_history: List[ChatMessage] = Field(
        default_factory=list,
        description="Previous messages in this conversation for context",
    )
    context: Optional[dict] = Field(
        default=None,
        description="Additional context (e.g., current dashboard data, selected site)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Analisis potensi angin di Pandeglang berdasarkan data terkini",
                    "conversation_history": [],
                    "context": {"site": "Pandeglang", "page": "wind-prediction"},
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """Response sent back to the frontend."""
    reply: str = Field(..., description="AI-generated response text")
    model: str = Field(..., description="Model used for generation")
    tokens_used: Optional[int] = Field(default=None, description="Total tokens consumed")
    processing_time_ms: Optional[float] = Field(default=None, description="Server-side latency in ms")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Standardized error response."""
    error: str
    detail: Optional[str] = None
    status_code: int
