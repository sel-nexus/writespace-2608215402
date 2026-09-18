"""Administrator account-management HTTP endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db_session
from app.errors import DomainError
from app.models import User
from app.schemas import UserCreate, UserOut
from app.services.admin import require_admin
from app.services.users import UserManagementError, UserManagementService

router = APIRouter(prefix="/api/users", tags=["users"])


class UserNotFoundError(DomainError):
    """Return a safe missing-user response."""

    status_code = 404
    code = "user_not_found"
    message = "The requested user was not found."


class UserProtectedError(DomainError):
    """Return a safe response when a protected account is selected."""

    status_code = 403
    code = "user_protected"
    message = "This account cannot be managed."


def get_admin_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Resolve an active administrator for account management.

    Args:
        current_user: Verified active authenticated account.

    Returns:
        Verified administrator account.
    """
    return require_admin(current_user)


@router.get("", response_model=list[UserOut], status_code=status.HTTP_200_OK, summary="List users")
def list_users(session: Annotated[Session, Depends(get_db_session)], _: Annotated[User, Depends(get_admin_user)]) -> list[UserOut]:
    """List safe user projections for an administrator."""
    return UserManagementService().list_users(session)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Create a user")
def create_user(payload: UserCreate, session: Annotated[Session, Depends(get_db_session)], _: Annotated[User, Depends(get_admin_user)]) -> UserOut:
    """Create a user or administrator with strict administrator-approved fields."""
    return UserManagementService().create(session, payload)


@router.patch("/{user_id}/deactivate", response_model=UserOut, status_code=status.HTTP_200_OK, summary="Deactivate a user")
def deactivate_user(user_id: int, session: Annotated[Session, Depends(get_db_session)], actor: Annotated[User, Depends(get_admin_user)]) -> UserOut:
    """Deactivate an eligible non-default account."""
    try:
        user = UserManagementService().deactivate(session, user_id, actor)
    except UserManagementError as exc:
        raise UserProtectedError() from exc
    if user is None:
        raise UserNotFoundError()
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user")
def delete_user(user_id: int, session: Annotated[Session, Depends(get_db_session)], actor: Annotated[User, Depends(get_admin_user)]) -> Response:
    """Delete an eligible user and retain their posts' snapshot attribution."""
    try:
        deleted = UserManagementService().delete(session, user_id, actor)
    except UserManagementError as exc:
        raise UserProtectedError() from exc
    if not deleted:
        raise UserNotFoundError()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
