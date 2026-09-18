"""Persistence operations for authentication users."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    """Query and persist user records using one supplied session."""

    def get_by_username(self, session: Session, username: str) -> User | None:
        """Find a user by case-insensitive normalized username.

        Args:
            session: Request-scoped database session.
            username: Candidate username.

        Returns:
            The matching user when present.
        """
        return session.scalar(select(User).where(func.lower(User.username) == username.lower()))

    def get_by_id(self, session: Session, user_id: int) -> User | None:
        """Find a user by primary key.

        Args:
            session: Request-scoped database session.
            user_id: Account identifier.

        Returns:
            The matching user when present.
        """
        return session.get(User, user_id)

    def create(self, session: Session, display_name: str, username: str, password_hash: str) -> User:
        """Persist a standard active user account.

        Args:
            session: Request-scoped database session.
            display_name: Public profile name.
            username: Normalized login identifier.
            password_hash: Bcrypt-protected password.

        Returns:
            The committed user.
        """
        user = User(display_name=display_name, username=username, password_hash=password_hash, role="user", is_default=False, is_active=True)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
