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

    def get_by_id(self, session: Session, post_id: int) -> Post | None:
        """Return one post by its persisted identifier when it exists."""
        return session.get(Post, post_id)

    def add(self, session: Session, post: Post) -> Post:
        """Persist a new post and refresh its server-derived fields."""
        session.add(post)
        session.commit()
        session.refresh(post)
        return post

    def save(self, session: Session, post: Post) -> Post:
        """Commit a changed post and refresh its persisted audit fields."""
        session.commit()
        session.refresh(post)
        return post

    def delete(self, session: Session, post: Post) -> None:
        """Remove a post permanently and commit the transaction."""
        session.delete(post)
        session.commit()
