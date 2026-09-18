"""Public, unauthenticated post-preview routes."""

from collections.abc import Generator
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database import get_session
from app.schemas import PublicPostPreview
from app.services.posts import PublicPostService

router = APIRouter(prefix="/api/public", tags=["public"])


def get_db_session(request: Request) -> Generator[Session, None, None]:
    """Yield a request-scoped database session from the application state."""
    yield from get_session(request.app.state.session_factory)


@router.get(
    "/posts",
    response_model=list[PublicPostPreview],
    status_code=200,
    summary="List public post previews",
)
def get_public_posts(
    session: Annotated[Session, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=3)] = 3,
) -> list[PublicPostPreview]:
    """Return one to three most-recent, safe public post previews."""
    return PublicPostService().list_previews(session, limit)
