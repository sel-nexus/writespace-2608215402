"""Business rules for safe public post previews."""

import re

from sqlalchemy.orm import Session

from app.repositories.posts import PostRepository
from app.schemas import PublicPostPreview


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
            PublicPostPreview(
                id=post.id,
                title=post.title,
                excerpt=self.make_excerpt(post.body),
                created_at=post.created_at,
            )
            for post in posts
        ]

    @staticmethod
    def make_excerpt(body: str) -> str:
        """Normalize whitespace and cap a preview body to 240 characters."""
        return re.sub(r"\s+", " ", body).strip()[:240]
