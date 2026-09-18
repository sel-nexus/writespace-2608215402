"""Strict Pydantic v2 schemas for the WriteSpace public API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PublicPostPreview(BaseModel):
    id: str = Field(strict=True, min_length=36, max_length=36)
    title: str = Field(strict=True, min_length=1, max_length=200)
    excerpt: str = Field(strict=True, max_length=240)
    created_at: datetime
    model_config = ConfigDict(from_attributes=True, extra="forbid", strict=True)


class PostWriteInput(BaseModel):
    title: str = Field(strict=True, min_length=1, max_length=200)
    content: str = Field(strict=True, min_length=1, max_length=50000)
    model_config = ConfigDict(extra="forbid", strict=True)

    @field_validator("title", "content")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field must not be blank.")
        return value


class PostAuthorOut(BaseModel):
    id: str | None
    display_name: str
    role: Literal["admin", "user"]
    model_config = ConfigDict(extra="forbid")


class PostOut(BaseModel):
    id: str = Field(min_length=36, max_length=36)
    title: str
    content: str
    excerpt: str
    author: PostAuthorOut | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(extra="forbid")


class UserRegister(BaseModel):
    display_name: str = Field(strict=True, min_length=1, max_length=120)
    username: str = Field(strict=True, min_length=3, max_length=50)
    password: str = Field(strict=True, min_length=8, max_length=128)
    confirm_password: str = Field(strict=True, min_length=8, max_length=128)
    model_config = ConfigDict(extra="forbid", strict=True)

    @field_validator("display_name", "username")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field must not be blank.")
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> "UserRegister":
        if self.password != self.confirm_password:
            raise ValueError("Password confirmation does not match.")
        return self


class LoginRequest(BaseModel):
    username: str = Field(strict=True, min_length=3, max_length=50)
    password: str = Field(strict=True, min_length=1, max_length=128)
    model_config = ConfigDict(extra="forbid", strict=True)

    @field_validator("username", "password")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        """Reject whitespace-only credentials before authentication work."""
        if not value.strip():
            raise ValueError("Field must not be blank.")
        return value


class UserOut(BaseModel):
    id: str = Field(min_length=36, max_length=36)
    display_name: str
    username: str
    role: Literal["admin", "user"]
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserCreate(BaseModel):
    display_name: str = Field(strict=True, min_length=1, max_length=120)
    username: str = Field(strict=True, min_length=3, max_length=50)
    password: str = Field(strict=True, min_length=8, max_length=128)
    role: Literal["admin", "user"]
    model_config = ConfigDict(extra="forbid", strict=True)

    @field_validator("display_name", "username")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field must not be blank.")
        return value


class AdminStatsOut(BaseModel):
    user_count: int = Field(ge=0)
    active_user_count: int = Field(ge=0)
    post_count: int = Field(ge=0)
    recent_posts: list[PostOut]
    model_config = ConfigDict(extra="forbid")


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    model_config = ConfigDict(extra="forbid")


class HealthResponse(BaseModel):
    status: str = Field(default="ok", strict=True)
    database: str = Field(default="reachable", strict=True)
    model_config = ConfigDict(extra="forbid", strict=True)


class HealthUnavailableResponse(BaseModel):
    status: str = Field(default="unavailable", strict=True)
    database: str = Field(default="unreachable", strict=True)
    model_config = ConfigDict(extra="forbid", strict=True)
