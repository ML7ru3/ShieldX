"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings
from app.exceptions import ApplicationException
from app.middleware.logging import log_requests_middleware
from app.api.v1.endpoints import health
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    # Add middleware
    add_middleware(app)

    # Add exception handlers
    add_exception_handlers(app)

    # Include routers
    add_routes(app)

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info(f"Environment: {settings.environment}")

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down application")

    return app


def add_middleware(app: FastAPI) -> None:
    """Add middleware to FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Custom middleware
    app.middleware("http")(log_requests_middleware)


def add_exception_handlers(app: FastAPI) -> None:
    """Add exception handlers to FastAPI application.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(ApplicationException)
    async def application_exception_handler(request, exc: ApplicationException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "message": "Validation error",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error",
                "details": None,
            },
        )


def add_routes(app: FastAPI) -> None:
    """Add API routes to FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # API v1 routes
    api_v1_router = FastAPI(title="v1")
    api_v1_router.include_router(health.router)

    app.include_router(
        api_v1_router.router,
        prefix=f"{settings.api_prefix}/{settings.api_version}",
    )

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs",
        }
