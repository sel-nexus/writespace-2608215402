"""ORM entities stored in the WriteSpace SQLite database."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for persisted audit fields."""
    return datetime.now(timezone.utc)


class User(Base):
    """A credential-bearing account identified by a public UUID string."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(id) = 36", name="ck_users_uuid"),
        CheckConstraint("length(trim(display_name)) BETWEEN 1 AND 120", name="ck_users_display_name"),
        CheckConstraint("length(trim(username)) BETWEEN 3 AND 50", name="ck_users_username"),
        CheckConstraint("role IN ('admin', 'user')", name="ck_users_role"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str] = mapped_column(String(50, collation="NOCASE"), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    is_default_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class Post(Base):
    """An editorial post whose immutable author snapshot survives account deletion."""

    __tablename__ = "posts"
    __table_args__ = (
        CheckConstraint("length(id) = 36", name="ck_posts_uuid"),
        CheckConstraint("length(trim(title)) BETWEEN 1 AND 200", name="ck_posts_title"),
        CheckConstraint("length(trim(content)) BETWEEN 1 AND 50000", name="ck_posts_content"),
        CheckConstraint("author_role IN ('admin', 'user')", name="ck_posts_author_role"),
        Index("ix_posts_created_id", "created_at", "id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    author_name: Mapped[str] = mapped_column(String(120), nullable=False)
    author_role: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    @property
    def body(self) -> str:
        """Provide the legacy public-reader alias without changing persistence."""
        return self.content
