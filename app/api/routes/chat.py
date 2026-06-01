"""
Chat API Router
================
Endpoints for AI chat interactions.
"""

from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.schemas.chat import ChatRequest, ChatResponse, ErrorResponse
from app.services.llm_service import get_llm_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to Mahi AI",
    description="Process a user message through the AI backend and return an intelligent response.",
    responses={
        200: {"model": ChatResponse, "description": "Successful AI response"},
        422: {"description": "Validation error — invalid request body"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.

    Accepts a user message with optional conversation history and dashboard context.
    Returns an AI-generated response tailored to wind energy analysis.
    """
    logger.info(f"Chat request received — message length: {len(request.message)}")

    try:
        llm_service = get_llm_service()

        result = await llm_service.generate_response(
            user_message=request.message,
            conversation_history=request.conversation_history,
            context=request.context,
        )

        response = ChatResponse(**result)
        logger.info(f"Chat response generated — model={response.model}, time={response.processing_time_ms}ms")

        return response

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
