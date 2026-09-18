"""Strict Pydantic v2 schemas for public API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PublicPostPreview(BaseModel):
    """Safe fields exposed for a public post preview."""

    id: int = Field(strict=True, ge=1)
    title: str = Field(strict=True, min_length=1, max_length=200)
    excerpt: str = Field(strict=True, max_length=240)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid", strict=True)


class PostWriteInput(BaseModel):
    """Strict editable fields accepted for a post mutation."""

    title: str = Field(strict=True, min_length=1, max_length=200)
    content: str = Field(strict=True, min_length=1, max_length=50000)

    model_config = ConfigDict(extra="forbid", strict=True)


class PostAuthorOut(BaseModel):
    """Safe author attribution for an authenticated post read."""

    id: int
    display_name: str
    role: str

    model_config = ConfigDict(extra="forbid")


class PostOut(BaseModel):
    """Safe full post projection for authenticated readers."""

    id: int = Field(ge=1)
    title: str
    content: str
    excerpt: str
    author: PostAuthorOut | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class UserRegister(BaseModel):
    """Strict public fields accepted to create a standard user."""

    display_name: str = Field(strict=True, min_length=1, max_length=120)
    username: str = Field(strict=True, min_length=3, max_length=50)
    password: str = Field(strict=True, min_length=8, max_length=128)
    confirm_password: str = Field(strict=True, min_length=8, max_length=128)

    model_config = ConfigDict(extra="forbid", strict=True)

    @field_validator("display_name")
    @classmethod
    def display_name_is_not_blank(cls, value: str) -> str:
        """Reject display names that contain only whitespace.

        Args:
            value: Submitted display name.

        Returns:
            The original validated display name.

        Raises:
            ValueError: If the name contains no visible characters.
        """
        if not value.strip():
            raise ValueError("Display name must not be blank.")
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> "UserRegister":
        """Reject a registration request with mismatched passwords.

        Raises:
            ValueError: If the confirmation does not match the password.
        """
        if self.password != self.confirm_password:
            raise ValueError("Password confirmation does not match.")
        return self


class LoginRequest(BaseModel):
    """Strict credentials accepted for a login attempt."""

    username: str = Field(strict=True, min_length=3, max_length=50)
    password: str = Field(strict=True, min_length=1, max_length=128)

    model_config = ConfigDict(extra="forbid", strict=True)


class UserOut(BaseModel):
    """Safe user projection that omits credentials and internal flags."""

    id: int
    display_name: str
    username: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AuthResponse(BaseModel):
    """Token response returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut

    model_config = ConfigDict(extra="forbid")


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
