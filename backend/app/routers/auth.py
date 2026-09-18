"""Authentication HTTP endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_db_session
from app.models import User
from app.schemas import AuthResponse, LoginRequest, UserOut, UserRegister
from app.services.auth import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, summary="Register an account")
def register(payload: UserRegister, session: Annotated[Session, Depends(get_db_session)], settings: Annotated[Settings, Depends(get_settings)]) -> AuthResponse:
    """Register a standard user and issue an access token.

    Args:
        payload: Strict validated registration values.
        session: Request-scoped database session.
        settings: Runtime JWT settings.

    Returns:
        Safe session payload.
    """
    return AuthService().register(session, payload, settings)


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK, summary="Log in")
def login(payload: LoginRequest, session: Annotated[Session, Depends(get_db_session)], settings: Annotated[Settings, Depends(get_settings)]) -> AuthResponse:
    """Authenticate an account and issue an access token.

    Args:
        payload: Login credentials.
        session: Request-scoped database session.
        settings: Runtime JWT settings.

    Returns:
        Safe session payload.
    """
    return AuthService().login(session, payload.username, payload.password, settings)


@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK, summary="Get current user")
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    """Return the current active user's safe profile.

    Args:
        current_user: Verified active user.

    Returns:
        Safe user projection.
    """
    return UserOut.model_validate(current_user)
