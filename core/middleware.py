from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, List
from datetime import datetime, timedelta
import time
from core.logging import logger
from core.config import settings


class RateLimitMiddleware:
    """
    Simple in-memory rate limiting middleware
    """
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}  # IP -> list of request timestamps
        self.window_size = settings.rate_limit_window  # in seconds
        self.max_requests = settings.rate_limit_requests  # max requests per window

    async def __call__(self, request: Request, call_next):
        # Get client IP address
        client_ip = request.client.host

        # Clean old requests outside the window
        now = time.time()
        if client_ip in self.requests:
            # Keep only requests within the time window
            self.requests[client_ip] = [
                timestamp for timestamp in self.requests[client_ip]
                if now - timestamp <= self.window_size
            ]
        else:
            self.requests[client_ip] = []

        # Check if rate limit is exceeded
        if len(self.requests[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"}
            )

        # Add current request timestamp
        self.requests[client_ip].append(now)

        # Process the request
        response = await call_next(request)
        return response


def add_rate_limiting(app):
    """
    Add rate limiting middleware to the FastAPI app
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    rate_limiter = RateLimitMiddleware()

    class RateLimitHTTPMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            return await rate_limiter(request, call_next)

    app.add_middleware(RateLimitHTTPMiddleware)
    return app