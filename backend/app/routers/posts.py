"""Authenticated post reading and writer CRUD HTTP endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db_session
from app.errors import DomainError
from app.models import User
from app.schemas import PostOut, PostWriteInput
from app.services.posts import PostForbiddenError, PostReadingService, PostWritingService

router = APIRouter(prefix="/api/posts", tags=["posts"])


class PostNotFoundError(DomainError):
    """Represent a safe missing-post response."""

    status_code = 404
    code = "post_not_found"
    message = "The requested post was not found."


class PostForbiddenDomainError(DomainError):
    """Represent a safe ownership failure without disclosing post details."""

    status_code = 403
    code = "post_forbidden"
    message = "You do not have permission to change this post."


@router.get("", response_model=list[PostOut], status_code=200, summary="List readable posts")
def list_posts(session: Annotated[Session, Depends(get_db_session)], _: Annotated[User, Depends(get_current_user)], limit: Annotated[int, Query(ge=1, le=100)] = 20) -> list[PostOut]:
    """Return a bounded, newest-first library for an authenticated reader."""
    return PostReadingService().list_posts(session, limit)


@router.post("", response_model=PostOut, status_code=201, summary="Create a post")
def create_post(input_data: PostWriteInput, session: Annotated[Session, Depends(get_db_session)], actor: Annotated[User, Depends(get_current_user)]) -> PostOut:
    """Create a post with author and audit fields derived from the active account."""
    return PostWritingService().create(session, input_data, actor)


@router.get("/{post_id}", response_model=PostOut, status_code=200, summary="Read a post")
def get_post(post_id: int, session: Annotated[Session, Depends(get_db_session)], _: Annotated[User, Depends(get_current_user)]) -> PostOut:
    """Return a safe full post or a safe missing-post envelope."""
    post = PostReadingService().get_post(session, post_id)
    if post is None:
        raise PostNotFoundError()
    return post


@router.put("/{post_id}", response_model=PostOut, status_code=200, summary="Update an owned post")
def update_post(post_id: int, input_data: PostWriteInput, session: Annotated[Session, Depends(get_db_session)], actor: Annotated[User, Depends(get_current_user)]) -> PostOut:
    """Update a post only for its owner or an administrator."""
    try:
        post = PostWritingService().update(session, post_id, input_data, actor)
    except PostForbiddenError as exc:
        raise PostForbiddenDomainError() from exc
    if post is None:
        raise PostNotFoundError()
    return post


@router.delete("/{post_id}", status_code=204, summary="Delete an owned post")
def delete_post(post_id: int, session: Annotated[Session, Depends(get_db_session)], actor: Annotated[User, Depends(get_current_user)]) -> Response:
    """Delete a post only for its owner or an administrator."""
    try:
        deleted = PostWritingService().delete(session, post_id, actor)
    except PostForbiddenError as exc:
        raise PostForbiddenDomainError() from exc
    if not deleted:
        raise PostNotFoundError()
    return Response(status_code=204)
