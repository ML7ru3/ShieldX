"""Health check endpoints."""

from fastapi import APIRouter
from app.config import settings
from app.models.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status response
    """
    return HealthResponse(
        status="healthy",
        message="Service is running",
        version=settings.api_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    """Readiness check endpoint.

    Returns:
        Readiness status response
    """
    return HealthResponse(
        status="ready",
        message="Service is ready to handle requests",
        version=settings.api_version,
        environment=settings.environment,
    )
