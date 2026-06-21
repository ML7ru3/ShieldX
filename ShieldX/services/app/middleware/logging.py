"""Request logging middleware."""

import time
from fastapi import Request
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def log_requests_middleware(request: Request, call_next):
    """Log incoming requests and response times.

    Args:
        request: FastAPI request object
        call_next: Next middleware or route handler

    Returns:
        Response with logging
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {process_time:.3f}s"
    )

    response.headers["X-Process-Time"] = str(process_time)
    return response
