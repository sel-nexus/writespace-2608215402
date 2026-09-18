"""Business rules for administrator-managed user accounts."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.errors import DuplicateUsernameError
from app.models import Post, User
from app.repositories.users import UserRepository
from app.schemas import UserCreate, UserOut


class UserManagementError(RuntimeError):
    """Signal that an account lifecycle action is not allowed."""


class UserManagementService:
    """Create and lifecycle-manage accounts after administrator authorization."""

    def __init__(self, users: UserRepository | None = None) -> None:
        """Initialize the service with a user repository.

        Args:
            users: Optional persistence dependency for composition.
        """
        self.users = users or UserRepository()

    def list_users(self, session: Session) -> list[UserOut]:
        """Return safe account projections in stable creation order.

        Args:
            session: Request-scoped database session.

        Returns:
            Safe user records without credentials or internal flags.
        """
        accounts = list(session.scalars(select(User).order_by(User.created_at.desc(), User.id.desc())))
        return [UserOut.model_validate(account) for account in accounts]

    def create(self, session: Session, payload: UserCreate) -> UserOut:
        """Persist a role-controlled account with a normalized username.

        Args:
            session: Request-scoped database session.
            payload: Strict administrator-supplied account values.

        Returns:
            The newly persisted safe user projection.

        Raises:
            DuplicateUsernameError: If the username already exists.
        """
        username = payload.username.lower()
        if self.users.get_by_username(session, username) is not None:
            raise DuplicateUsernameError()
        account = User(
            display_name=payload.display_name.strip(),
            username=username,
            password_hash=hash_password(payload.password),
            role=payload.role,
            is_default=False,
            is_active=True,
        )
        try:
            session.add(account)
            session.commit()
            session.refresh(account)
        except IntegrityError as exc:
            session.rollback()
            raise DuplicateUsernameError() from exc
        return UserOut.model_validate(account)

    def deactivate(self, session: Session, user_id: int, actor: User) -> UserOut | None:
        """Deactivate an eligible account without permitting protected targets.

        Args:
            session: Request-scoped database session.
            user_id: Account to deactivate.
            actor: Verified administrator performing the operation.

        Returns:
            Updated safe account projection, or None if absent.

        Raises:
            UserManagementError: If the target is the actor or default admin.
        """
        target = self.users.get_by_id(session, user_id)
        if target is None:
            return None
        self._require_eligible_target(target, actor)
        target.is_active = False
        session.commit()
        session.refresh(target)
        return UserOut.model_validate(target)

    def delete(self, session: Session, user_id: int, actor: User) -> bool:
        """Delete an eligible account while preserving its post attribution snapshots.

        Args:
            session: Request-scoped database session.
            user_id: Account to remove.
            actor: Verified administrator performing the operation.

        Returns:
            True when a record was deleted, otherwise False.

        Raises:
            UserManagementError: If the target is the actor or default admin.
        """
        target = self.users.get_by_id(session, user_id)
        if target is None:
            return False
        self._require_eligible_target(target, actor)
        for post in session.scalars(select(Post).where(Post.author_id == target.id)):
            post.author_id = None
            post.author_display_name = post.author_display_name or target.display_name
            post.author_role = post.author_role or target.role
        session.delete(target)
        session.commit()
        return True

    @staticmethod
    def _require_eligible_target(target: User, actor: User) -> None:
        """Reject self-management and any mutation of the default administrator.

        Args:
            target: Account selected for lifecycle management.
            actor: Verified administrator making the request.

        Raises:
            UserManagementError: If the target is protected.
        """
        if target.id == actor.id or target.is_default:
            raise UserManagementError()
