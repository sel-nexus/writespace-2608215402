"""Business rules for registration, login, and safe user projection."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.auth.passwords import DUMMY_HASH, hash_password, verify_password
from app.config import Settings
from app.errors import DuplicateUsernameError, InvalidCredentialsError
from app.models import User
from app.repositories.users import UserRepository
from app.schemas import AuthResponse, UserOut, UserRegister


class AuthService:
    """Coordinate user persistence with password and token services."""

    def __init__(self, users: UserRepository | None = None) -> None:
        """Initialize the service with a repository.

        Args:
            users: Optional repository override for composition.
        """
        self.users = users or UserRepository()

    def register(self, session: Session, payload: UserRegister, settings: Settings) -> AuthResponse:
        """Create a user and return a signed session payload.

        Args:
            session: Request-scoped database session.
            payload: Validated registration request.
            settings: Runtime JWT settings.

        Returns:
            Signed session response containing only safe user fields.

        Raises:
            DuplicateUsernameError: If the username is already registered.
        """
        username = payload.username.lower()
        if username == "admin" or self.users.get_by_username(session, username) is not None:
            raise DuplicateUsernameError()
        try:
            user = self.users.create(session, payload.display_name.strip(), username, hash_password(payload.password))
        except IntegrityError as exc:
            session.rollback()
            raise DuplicateUsernameError() from exc
        return self._auth_response(user, settings)

    def login(self, session: Session, username: str, password: str, settings: Settings) -> AuthResponse:
        """Authenticate an active account without disclosing failure reason.

        Args:
            session: Request-scoped database session.
            username: Login identifier.
            password: Candidate password.
            settings: Runtime JWT settings.

        Returns:
            Signed session response containing safe fields.

        Raises:
            InvalidCredentialsError: If credentials are unknown, incorrect, or inactive.
        """
        user = self.users.get_by_username(session, username.lower())
        password_hash = user.password_hash if user is not None else DUMMY_HASH
        valid_password = verify_password(password, password_hash)
        if user is None or not user.is_active or not valid_password:
            raise InvalidCredentialsError()
        return self._auth_response(user, settings)

    def _auth_response(self, user: User, settings: Settings) -> AuthResponse:
        """Build a safe token response for an authenticated user.

        Args:
            user: Authenticated persisted account.
            settings: Runtime JWT settings.

        Returns:
            Safe authentication payload.
        """
        return AuthResponse(access_token=create_access_token(user.id, user.role, settings), user=UserOut.model_validate(user))
