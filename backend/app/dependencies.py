"""FastAPI dependencies for sessions and authenticated users."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_access_token
from app.config import Settings, get_settings
from app.database import get_session
from app.errors import InvalidTokenError
from app.models import User
from app.repositories.users import UserRepository

_bearer = HTTPBearer(auto_error=False)


def get_db_session(request: Request) -> Generator[Session, None, None]:
    """Yield the request-scoped database session.

    Args:
        request: Active FastAPI request.

    Yields:
        A session bound to the application's database.
    """
    yield from get_session(request.app.state.session_factory)


def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)], session: Annotated[Session, Depends(get_db_session)], settings: Annotated[Settings, Depends(get_settings)]) -> User:
    """Resolve an active database user from a verified bearer token.

    Args:
        credentials: Parsed bearer credentials when supplied.
        session: Request-scoped database session.
        settings: Runtime JWT settings.

    Returns:
        The active token subject.

    Raises:
        InvalidTokenError: If credentials or the account are invalid.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidTokenError()
    claims = decode_access_token(credentials.credentials, settings)
    try:
        user_id = int(str(claims["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidTokenError() from exc
    user = UserRepository().get_by_id(session, user_id)
    if user is None or not user.is_active:
        raise InvalidTokenError()
    return user
