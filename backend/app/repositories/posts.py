"""Database queries for WriteSpace posts."""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import Post


class PostRepository:
    def list_recent(self, session: Session, limit: int) -> list[Post]:
        """Return newest posts ordered by UTC timestamp then UUID."""
        statement: Select[tuple[Post]] = select(Post).order_by(Post.created_at.desc(), Post.id.desc()).limit(limit)
        return list(session.scalars(statement))

    def get_by_id(self, session: Session, post_id: str) -> Post | None:
        """Return one post by its UUID primary key."""
        return session.get(Post, post_id)

    def add(self, session: Session, post: Post) -> Post:
        session.add(post)
        session.commit()
        session.refresh(post)
        return post

    def save(self, session: Session, post: Post) -> Post:
        session.commit()
        session.refresh(post)
        return post

    def delete(self, session: Session, post: Post) -> None:
        session.delete(post)
        session.commit()
