"""Business rules for public previews, reading, and post mutations."""

import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Post, User
from app.repositories.posts import PostRepository
from app.schemas import PostAuthorOut, PostOut, PostWriteInput, PublicPostPreview


class PostForbiddenError(RuntimeError):
    """Signal that an authenticated user cannot mutate the requested post."""


class PublicPostService:
    def __init__(self, repository: PostRepository | None = None) -> None:
        self._repository = repository or PostRepository()

    def list_previews(self, session: Session, limit: int) -> list[PublicPostPreview]:
        posts = self._repository.list_recent(session, min(max(limit, 1), 3))
        return [PublicPostPreview(id=post.id, title=post.title, excerpt=self.make_excerpt(post.content), created_at=post.created_at) for post in posts]

    @staticmethod
    def make_excerpt(content: str) -> str:
        return re.sub(r"\s+", " ", content).strip()[:240]


class PostReadingService:
    def __init__(self, repository: PostRepository | None = None) -> None:
        self._repository = repository or PostRepository()

    def list_posts(self, session: Session, limit: int) -> list[PostOut]:
        return [self._to_post_out(post) for post in self._repository.list_recent(session, limit)]

    def get_post(self, session: Session, post_id: str) -> PostOut | None:
        post = self._repository.get_by_id(session, post_id)
        return self._to_post_out(post) if post is not None else None

    @staticmethod
    def _to_post_out(post: Post) -> PostOut:
        return PostOut(id=post.id, title=post.title, content=post.content, excerpt=PublicPostService.make_excerpt(post.content), author=PostAuthorOut(id=post.author_id, display_name=post.author_name, role=post.author_role), created_at=post.created_at, updated_at=post.updated_at)


class PostWritingService:
    def __init__(self, repository: PostRepository | None = None) -> None:
        self._repository = repository or PostRepository()

    def create(self, session: Session, input_data: PostWriteInput, author: User) -> PostOut:
        now = datetime.now(timezone.utc)
        post = Post(title=input_data.title, content=input_data.content, author_id=author.id, author_name=author.display_name, author_role=author.role, created_at=now, updated_at=now)
        return PostReadingService._to_post_out(self._repository.add(session, post))

    def update(self, session: Session, post_id: str, input_data: PostWriteInput, actor: User) -> PostOut | None:
        post = self._repository.get_by_id(session, post_id)
        if post is None:
            return None
        self._require_owner_or_admin(post, actor)
        post.title = input_data.title
        post.content = input_data.content
        post.updated_at = datetime.now(timezone.utc)
        return PostReadingService._to_post_out(self._repository.save(session, post))

    def delete(self, session: Session, post_id: str, actor: User) -> bool:
        post = self._repository.get_by_id(session, post_id)
        if post is None:
            return False
        self._require_owner_or_admin(post, actor)
        self._repository.delete(session, post)
        return True

    @staticmethod
    def _require_owner_or_admin(post: Post, actor: User) -> None:
        if post.author_id != actor.id and actor.role != "admin":
            raise PostForbiddenError()
