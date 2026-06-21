"""Base service class."""

from app.utils.logger import get_logger


class BaseService:
    """Base service with common functionality."""

    def __init__(self):
        """Initialize service."""
        self.logger = get_logger(self.__class__.__name__)

    async def health_check(self) -> dict[str, str]:
        """Health check for the service.

        Returns:
            Health status dictionary
        """
        return {"status": "healthy"}
