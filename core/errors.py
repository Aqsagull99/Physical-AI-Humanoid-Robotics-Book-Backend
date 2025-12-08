from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from core.logging import logger
import traceback
from typing import Dict, Any

class RAGChatbotError(Exception):
    """Base exception class for RAG Chatbot application"""
    def __init__(self, message: str, status_code: int = 500, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

async def error_handler(request: Request, exc: Exception):
    """
    Global error handler for the application
    """
    logger.error(f"Error occurred: {str(exc)}", exc_info=True)

    if isinstance(exc, RAGChatbotError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "details": exc.details,
                "status_code": exc.status_code
            }
        )
    elif isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code
            }
        )
    else:
        # Log the full traceback for unexpected errors
        error_trace = traceback.format_exc()
        logger.error(f"Unexpected error: {error_trace}")

        return JSONResponse(
            status_code=500,
            content={
                "error": "An internal server error occurred",
                "status_code": 500
            }
        )

# Register the error handler in main.py
def register_error_handlers(app):
    """
    Register error handlers with the FastAPI app
    """
    app.add_exception_handler(Exception, error_handler)
    return app