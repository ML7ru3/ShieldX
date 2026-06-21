"""Custom application exceptions."""

from typing import Any


class ApplicationException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        """Initialize exception.

        Args:
            message: Exception message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(ApplicationException):
    """Validation error exception."""

    def __init__(self, message: str = "Validation failed", details: dict[str, Any] | None = None):
        """Initialize validation exception."""
        super().__init__(message, status_code=422, details=details)


class ResourceNotFoundException(ApplicationException):
    """Resource not found exception."""

    def __init__(self, resource: str, details: dict[str, Any] | None = None):
        """Initialize not found exception."""
        message = f"{resource} not found"
        super().__init__(message, status_code=404, details=details)


class UnauthorizedException(ApplicationException):
    """Unauthorized exception."""

    def __init__(self, message: str = "Unauthorized", details: dict[str, Any] | None = None):
        """Initialize unauthorized exception."""
        super().__init__(message, status_code=401, details=details)


class ForbiddenException(ApplicationException):
    """Forbidden exception."""

    def __init__(self, message: str = "Forbidden", details: dict[str, Any] | None = None):
        """Initialize forbidden exception."""
        super().__init__(message, status_code=403, details=details)


class InternalServerException(ApplicationException):
    """Internal server error exception."""

    def __init__(self, message: str = "Internal server error", details: dict[str, Any] | None = None):
        """Initialize internal server error exception."""
        super().__init__(message, status_code=500, details=details)
