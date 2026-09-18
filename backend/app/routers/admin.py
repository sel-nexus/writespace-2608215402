"""Administrator statistics HTTP endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db_session
from app.models import User
from app.schemas import AdminStatsOut
from app.services.admin import AdminService, require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_admin_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Resolve an active administrator for statistics access.

    Args:
        current_user: Verified active authenticated account.

    Returns:
        Verified administrator account.
    """
    return require_admin(current_user)


@router.get("/stats", response_model=AdminStatsOut, status_code=status.HTTP_200_OK, summary="Get administration statistics")
def get_stats(session: Annotated[Session, Depends(get_db_session)], _: Annotated[User, Depends(get_admin_user)]) -> AdminStatsOut:
    """Return server-derived account and post statistics to an administrator."""
    return AdminService().get_stats(session)
