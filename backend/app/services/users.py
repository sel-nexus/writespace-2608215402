"""Business rules for administrator-managed UUID user accounts."""

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
    def __init__(self, users: UserRepository | None = None) -> None:
        self.users = users or UserRepository()

    def list_users(self, session: Session) -> list[UserOut]:
        return [UserOut.model_validate(account) for account in session.scalars(select(User).order_by(User.created_at.desc(), User.id.desc()))]

    def create(self, session: Session, payload: UserCreate) -> UserOut:
        username = payload.username.strip().lower()
        if self.users.get_by_username(session, username) is not None:
            raise DuplicateUsernameError()
        account = User(display_name=payload.display_name.strip(), username=username, password_hash=hash_password(payload.password), role=payload.role, is_default_admin=False, is_active=True)
        try:
            session.add(account)
            session.commit()
            session.refresh(account)
        except IntegrityError as exc:
            session.rollback()
            raise DuplicateUsernameError() from exc
        return UserOut.model_validate(account)

    def deactivate(self, session: Session, user_id: str, actor: User) -> UserOut | None:
        target = self.users.get_by_id(session, user_id)
        if target is None:
            return None
        self._require_eligible_target(target, actor)
        target.is_active = False
        session.commit()
        session.refresh(target)
        return UserOut.model_validate(target)

    def delete(self, session: Session, user_id: str, actor: User) -> bool:
        target = self.users.get_by_id(session, user_id)
        if target is None:
            return False
        self._require_eligible_target(target, actor)
        for post in session.scalars(select(Post).where(Post.author_id == target.id)):
            post.author_id = None
        session.delete(target)
        session.commit()
        return True

    @staticmethod
    def _require_eligible_target(target: User, actor: User) -> None:
        if target.id == actor.id or target.is_default_admin:
            raise UserManagementError()
