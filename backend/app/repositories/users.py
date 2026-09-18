"""Persistence operations for UUID-identified authentication users."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def get_by_username(self, session: Session, username: str) -> User | None:
        """Find a user by case-insensitive normalized username."""
        return session.scalar(select(User).where(func.lower(User.username) == username.lower()))

    def get_by_id(self, session: Session, user_id: str) -> User | None:
        """Find a user by UUID primary key."""
        return session.get(User, user_id)

    def create(self, session: Session, display_name: str, username: str, password_hash: str) -> User:
        """Persist a standard active user account."""
        user = User(display_name=display_name, username=username, password_hash=password_hash, role="user", is_default_admin=False, is_active=True)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
