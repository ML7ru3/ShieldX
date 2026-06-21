"""API v1 dependencies."""

from fastapi import Depends, HTTPException, status
from typing import Generator

from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_current_user(user_id: str | None = None) -> dict:
    """Get current user from request.

    Args:
        user_id: Optional user ID

    Returns:
        User information

    Raises:
        HTTPException: If user is not authenticated
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return {"user_id": user_id}
