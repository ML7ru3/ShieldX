"""Response schemas and models."""

from pydantic import BaseModel, Field
from typing import Any, Generic, TypeVar


T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base response model."""

    status: str = Field(default="success", description="Response status")
    message: str = Field(default="Operation successful", description="Response message")


class DataResponse(BaseResponse, Generic[T]):
    """Generic data response model."""

    data: T | None = Field(default=None, description="Response data")


class HealthResponse(BaseResponse):
    """Health check response."""

    version: str = Field(description="API version")
    environment: str = Field(description="Environment")


class ErrorResponse(BaseModel):
    """Error response model."""

    status: str = Field(default="error", description="Error status")
    message: str = Field(description="Error message")
    details: dict[str, Any] | None = Field(default=None, description="Error details")
