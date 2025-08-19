"""
Global error handling middleware
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.utils.logger import get_logger
import traceback

logger = get_logger(__name__)


def add_exception_handlers(app: FastAPI):
    """
    Add exception handlers to the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        logger.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle value errors"""
        logger.error(
            "Value error",
            error=str(exc),
            path=request.url.path,
            traceback=traceback.format_exc()
        )
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions"""
        logger.error(
            "Unhandled exception",
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
            traceback=traceback.format_exc()
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred"}
        )
