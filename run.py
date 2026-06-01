"""
Application Entry Point
========================
Run with: python -m uvicorn run:app --reload
Or:       python run.py
"""

import uvicorn

from app.main import create_app
from app.core.config import get_settings

# Create the application instance
app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "run:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
