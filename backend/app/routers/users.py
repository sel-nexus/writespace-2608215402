"""Administrator account-management HTTP endpoints."""

from typing import Annotated
from uuid import UUID

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
    status_code = 404
    code = "user_not_found"
    message = "The requested user was not found."


class UserProtectedError(DomainError):
    status_code = 403
    code = "user_protected"
    message = "This account cannot be managed."


def get_admin_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return require_admin(current_user)


@router.get("", response_model=list[UserOut], status_code=status.HTTP_200_OK, summary="List users")
def list_users(session: Annotated[Session, Depends(get_db_session)], _: Annotated[User, Depends(get_admin_user)]) -> list[UserOut]:
    return UserManagementService().list_users(session)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Create a user")
def create_user(payload: UserCreate, session: Annotated[Session, Depends(get_db_session)], _: Annotated[User, Depends(get_admin_user)]) -> UserOut:
    return UserManagementService().create(session, payload)


@router.patch("/{user_id}/deactivate", response_model=UserOut, status_code=status.HTTP_200_OK, summary="Deactivate a user")
def deactivate_user(user_id: UUID, session: Annotated[Session, Depends(get_db_session)], actor: Annotated[User, Depends(get_admin_user)]) -> UserOut:
    try:
        user = UserManagementService().deactivate(session, str(user_id), actor)
    except UserManagementError as exc:
        raise UserProtectedError() from exc
    if user is None:
        raise UserNotFoundError()
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user")
def delete_user(user_id: UUID, session: Annotated[Session, Depends(get_db_session)], actor: Annotated[User, Depends(get_admin_user)]) -> Response:
    try:
        deleted = UserManagementService().delete(session, str(user_id), actor)
    except UserManagementError as exc:
        raise UserProtectedError() from exc
    if not deleted:
        raise UserNotFoundError()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
