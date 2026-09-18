"""Database queries for publicly readable post previews."""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import Post


class PostRepository:
    """Repository responsible for ordered post reads."""

    def list_recent(self, session: Session, limit: int) -> list[Post]:
        """Return the most recently created posts up to the supplied limit."""
        statement: Select[tuple[Post]] = (
            select(Post).order_by(Post.created_at.desc(), Post.id.desc()).limit(limit)
        )
        return list(session.scalars(statement))
