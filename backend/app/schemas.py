"""Strict Pydantic v2 schemas for public API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PublicPostPreview(BaseModel):
    """Safe fields exposed for a public post preview."""

    id: int = Field(strict=True, ge=1)
    title: str = Field(strict=True, min_length=1, max_length=200)
    excerpt: str = Field(strict=True, max_length=240)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid", strict=True)


class HealthResponse(BaseModel):
    """Safe health response returned when the database is reachable."""

    status: str = Field(default="ok", strict=True)
    database: str = Field(default="reachable", strict=True)

    model_config = ConfigDict(extra="forbid", strict=True)


class HealthUnavailableResponse(BaseModel):
    """Safe health response returned when the database cannot be reached."""

    status: str = Field(default="unavailable", strict=True)
    database: str = Field(default="unreachable", strict=True)

    model_config = ConfigDict(extra="forbid", strict=True)
