"""Administrator authorization and server-derived statistics."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import Post, User
from app.schemas import AdminStatsOut
from app.services.posts import PostReadingService


class AdminForbiddenError(DomainError):
    """Return a safe response when an active user lacks administrator access."""

    status_code = 403
    code = "admin_forbidden"
    message = "Administrator access is required."


def require_admin(user: User) -> User:
    """Fail closed unless the resolved active account has the administrator role.

    Args:
        user: Active account resolved by the authentication dependency.

    Returns:
        The same verified administrator account.

    Raises:
        AdminForbiddenError: If the account does not hold the administrator role.
    """
    if user.role != "admin":
        raise AdminForbiddenError()
    return user


class AdminService:
    """Produce administration data from database-side aggregate queries."""

    def get_stats(self, session: Session) -> AdminStatsOut:
        """Return counts and the five newest safe post projections.

        Args:
            session: Request-scoped database session.

        Returns:
            Server-derived statistics and latest post projections.
        """
        user_count = session.scalar(select(func.count()).select_from(User)) or 0
        active_user_count = session.scalar(select(func.count()).select_from(User).where(User.is_active.is_(True))) or 0
        post_count = session.scalar(select(func.count()).select_from(Post)) or 0
        recent_posts = PostReadingService().list_posts(session, 5)
        return AdminStatsOut(
            user_count=user_count,
            active_user_count=active_user_count,
            post_count=post_count,
            recent_posts=recent_posts,
        )
