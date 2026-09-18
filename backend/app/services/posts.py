"""Business rules for public previews, reading, and author-controlled post mutations."""

import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Post, User
from app.repositories.posts import PostRepository
from app.schemas import PostAuthorOut, PostOut, PostWriteInput, PublicPostPreview


class PostForbiddenError(RuntimeError):
    """Signal that an authenticated user cannot mutate the requested post."""


class PublicPostService:
    """Maps ordered posts into bounded, public-safe previews."""

    def __init__(self, repository: PostRepository | None = None) -> None:
        """Initialize the service with a repository or the default repository."""
        self._repository = repository or PostRepository()

    def list_previews(self, session: Session, limit: int) -> list[PublicPostPreview]:
        """Return no more than three ordered previews without private fields."""
        bounded_limit = min(max(limit, 1), 3)
        posts = self._repository.list_recent(session, bounded_limit)
        return [
            PublicPostPreview(id=post.id, title=post.title, excerpt=self.make_excerpt(post.body), created_at=post.created_at)
            for post in posts
        ]

    @staticmethod
    def make_excerpt(body: str) -> str:
        """Normalize whitespace and cap a preview body to 240 characters."""
        return re.sub(r"\s+", " ", body).strip()[:240]


class PostReadingService:
    """Maps persisted posts into safe authenticated reading projections."""

    def __init__(self, repository: PostRepository | None = None) -> None:
        """Initialize the service with a repository or the default repository."""
        self._repository = repository or PostRepository()

    def list_posts(self, session: Session, limit: int) -> list[PostOut]:
        """Return bounded full post projections in deterministic newest-first order."""
        return [self._to_post_out(post) for post in self._repository.list_recent(session, limit)]

    def get_post(self, session: Session, post_id: int) -> PostOut | None:
        """Return a full safe projection for a persisted post when it exists."""
        post = self._repository.get_by_id(session, post_id)
        return self._to_post_out(post) if post is not None else None

    @staticmethod
    def _to_post_out(post: Post) -> PostOut:
        """Build the reading contract from persisted content and author snapshot."""
        author = None
        if post.author_id is not None and post.author_display_name and post.author_role:
            author = PostAuthorOut(id=post.author_id, display_name=post.author_display_name, role=post.author_role)
        return PostOut(id=post.id, title=post.title, content=post.body, excerpt=PublicPostService.make_excerpt(post.body), author=author, created_at=post.created_at, updated_at=post.updated_at)


class PostWritingService:
    """Persists post mutations after enforcing author or administrator ownership."""

    def __init__(self, repository: PostRepository | None = None) -> None:
        """Initialize the service with a repository or the default repository."""
        self._repository = repository or PostRepository()

    def create(self, session: Session, input_data: PostWriteInput, author: User) -> PostOut:
        """Persist a post with all attribution and timestamps derived server-side."""
        now = datetime.now(timezone.utc)
        post = Post(title=input_data.title, body=input_data.content, author_id=author.id, author_display_name=author.display_name, author_role=author.role, created_at=now, updated_at=now)
        return PostReadingService._to_post_out(self._repository.add(session, post))

    def update(self, session: Session, post_id: int, input_data: PostWriteInput, actor: User) -> PostOut | None:
        """Update a post when the actor owns it or currently has the administrator role."""
        post = self._repository.get_by_id(session, post_id)
        if post is None:
            return None
        self._require_owner_or_admin(post, actor)
        post.title = input_data.title
        post.body = input_data.content
        post.updated_at = datetime.now(timezone.utc)
        return PostReadingService._to_post_out(self._repository.save(session, post))

    def delete(self, session: Session, post_id: int, actor: User) -> bool:
        """Delete a post when the actor owns it or currently has the administrator role."""
        post = self._repository.get_by_id(session, post_id)
        if post is None:
            return False
        self._require_owner_or_admin(post, actor)
        self._repository.delete(session, post)
        return True

    @staticmethod
    def _require_owner_or_admin(post: Post, actor: User) -> None:
        """Reject mutations from users who are neither the post owner nor an administrator."""
        if post.author_id != actor.id and actor.role != "admin":
            raise PostForbiddenError()
