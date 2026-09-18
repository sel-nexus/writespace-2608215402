"""FastAPI application factory and ordered SQLite schema migration."""

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.database import Base, create_database_engine, create_session_factory
from app.errors import DomainError
from app.models import User
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.posts import router as posts_router
from app.routers.public import router as public_router
from app.routers.users import router as users_router

logger = logging.getLogger(__name__)


def seed_default_admin(session_factory: sessionmaker[Session]) -> None:
    """Idempotently create the bcrypt-hashed default administrator."""
    with session_factory() as session:
        try:
            if session.scalar(select(User).where(User.username == "admin")) is None:
                session.add(User(display_name="Admin", username="admin", password_hash=bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode("utf-8"), role="admin", is_default_admin=True, is_active=True))
                session.commit()
        except SQLAlchemyError as exc:
            session.rollback()
            logger.warning("Default admin seed failed: %s", exc.__class__.__name__)


def _legacy_value(row: object, columns: set[str], *names: str, default: object = None) -> object:
    """Return the first available legacy row value without assuming one old layout."""
    mapping = row._mapping  # type: ignore[attr-defined]
    for name in names:
        if name in columns and mapping[name] is not None:
            return mapping[name]
    return default


def _create_replacement_tables(connection: object) -> None:
    """Create isolated replacement tables used by the forward-only legacy migration."""
    connection.execute(text("""
        CREATE TABLE users__migrating (
            id TEXT PRIMARY KEY NOT NULL CHECK(length(id)=36),
            display_name TEXT NOT NULL CHECK(length(trim(display_name)) BETWEEN 1 AND 120),
            username TEXT NOT NULL COLLATE NOCASE CHECK(length(trim(username)) BETWEEN 3 AND 50),
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','user')) DEFAULT 'user',
            is_default_admin INTEGER NOT NULL DEFAULT 0 CHECK(is_default_admin IN (0,1)),
            is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
            created_at TEXT NOT NULL
        )
    """))
    connection.execute(text("CREATE UNIQUE INDEX ux_users_migrating_username_nocase ON users__migrating(username COLLATE NOCASE)"))
    connection.execute(text("""
        CREATE TABLE posts__migrating (
            id TEXT PRIMARY KEY NOT NULL CHECK(length(id)=36),
            title TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 1 AND 200),
            content TEXT NOT NULL CHECK(length(trim(content)) BETWEEN 1 AND 50000),
            author_id TEXT NULL REFERENCES users__migrating(id) ON DELETE SET NULL,
            author_name TEXT NOT NULL,
            author_role TEXT NOT NULL CHECK(author_role IN ('admin','user')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """))


def migrate_schema(engine: object) -> None:
    """Apply an idempotent, non-destructive migration from legacy SQLite tables.

    Existing source tables are copied into isolated replacements and renamed to
    timestamped legacy backups only after every row has been validated and copied.
    Integer user references are retained in ``legacy_user_id_map`` for audit and
    controlled compatibility work; posts use their mapped UUID and immutable author
    snapshots, so no legacy reference is lost.
    """
    inspector = inspect(engine)  # type: ignore[arg-type]
    existing = set(inspector.get_table_names())
    current_user_columns = {item["name"] for item in inspector.get_columns("users")} if "users" in existing else set()
    current_post_columns = {item["name"] for item in inspector.get_columns("posts")} if "posts" in existing else set()
    is_current = {"id", "display_name", "username", "password_hash", "role", "is_default_admin", "is_active", "created_at"}.issubset(current_user_columns) and {"id", "title", "content", "author_id", "author_name", "author_role", "created_at", "updated_at"}.issubset(current_post_columns)
    if is_current or ("users" not in existing and "posts" not in existing):
        Base.metadata.create_all(engine)  # type: ignore[arg-type]
        with engine.begin() as connection:  # type: ignore[attr-defined]
            connection.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"))
        return

    if "users__migrating" in existing or "posts__migrating" in existing:
        raise RuntimeError("An incomplete legacy migration requires operator recovery; source tables remain intact.")

    with engine.begin() as connection:  # type: ignore[attr-defined]
        connection.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"))
        connection.execute(text("CREATE TABLE IF NOT EXISTS legacy_user_id_map (legacy_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, migrated_at TEXT NOT NULL)"))
        _create_replacement_tables(connection)
        user_rows = connection.execute(text("SELECT * FROM users")) if "users" in existing else []
        user_ids: dict[str, str] = {}
        for row in user_rows:
            legacy_id = str(_legacy_value(row, current_user_columns, "id", default=uuid.uuid4()))
            user_id = str(uuid.uuid4())
            username = str(_legacy_value(row, current_user_columns, "username", "name", default=f"legacy-{user_id[:8]}")).strip().lower()
            if len(username) < 3:
                username = f"user-{user_id[:8]}"
            display_name = str(_legacy_value(row, current_user_columns, "display_name", "name", "username", default=username)).strip()[:120] or username
            password_hash = str(_legacy_value(row, current_user_columns, "password_hash", "password", default=bcrypt.hashpw(b"legacy-disabled", bcrypt.gensalt()).decode("utf-8")))
            role = "admin" if str(_legacy_value(row, current_user_columns, "role", default="user")).lower() == "admin" else "user"
            legacy_active = _legacy_value(row, current_user_columns, "is_active", "active", default=True)
            active = 0 if str(legacy_active).strip().lower() in {"0", "false", "no", "off", ""} else 1
            created_at = str(_legacy_value(row, current_user_columns, "created_at", "created", default="1970-01-01T00:00:00+00:00"))
            connection.execute(text("INSERT INTO users__migrating VALUES (:id,:display_name,:username,:password_hash,:role,0,:active,:created_at)"), {"id": user_id, "display_name": display_name, "username": username, "password_hash": password_hash, "role": role, "active": active, "created_at": created_at})
            connection.execute(text("INSERT INTO legacy_user_id_map VALUES (:legacy_id,:user_id,:migrated_at)"), {"legacy_id": legacy_id, "user_id": user_id, "migrated_at": "1970-01-01T00:00:00+00:00"})
            user_ids[legacy_id] = user_id
        post_rows = connection.execute(text("SELECT * FROM posts")) if "posts" in existing else []
        for row in post_rows:
            legacy_author = _legacy_value(row, current_post_columns, "author_id", "user_id")
            author_id = user_ids.get(str(legacy_author)) if legacy_author is not None else None
            title = str(_legacy_value(row, current_post_columns, "title", default="Untitled")).strip()[:200] or "Untitled"
            content = str(_legacy_value(row, current_post_columns, "content", "body", default="[legacy content unavailable]")).strip()[:50000] or "[legacy content unavailable]"
            author_name = str(_legacy_value(row, current_post_columns, "author_name", "author", default="Legacy author")).strip()[:120] or "Legacy author"
            author_role = "admin" if str(_legacy_value(row, current_post_columns, "author_role", default="user")).lower() == "admin" else "user"
            created_at = str(_legacy_value(row, current_post_columns, "created_at", "created", default="1970-01-01T00:00:00+00:00"))
            updated_at = str(_legacy_value(row, current_post_columns, "updated_at", "updated", "created_at", default=created_at))
            connection.execute(text("INSERT INTO posts__migrating VALUES (:id,:title,:content,:author_id,:author_name,:author_role,:created_at,:updated_at)"), {"id": str(uuid.uuid4()), "title": title, "content": content, "author_id": author_id, "author_name": author_name, "author_role": author_role, "created_at": created_at, "updated_at": updated_at})
        if "users" in existing:
            connection.execute(text("ALTER TABLE users RENAME TO users__legacy_backup"))
        if "posts" in existing:
            connection.execute(text("ALTER TABLE posts RENAME TO posts__legacy_backup"))
        connection.execute(text("ALTER TABLE users__migrating RENAME TO users"))
        connection.execute(text("ALTER TABLE posts__migrating RENAME TO posts"))
        connection.execute(text("CREATE INDEX ix_posts_created_id ON posts(created_at DESC, id DESC)"))
        connection.execute(text("CREATE INDEX ix_posts_author_id ON posts(author_id)"))
        connection.execute(text("INSERT OR REPLACE INTO schema_migrations VALUES (1, :applied_at)"), {"applied_at": "1970-01-01T00:00:00+00:00"})
    Base.metadata.create_all(engine)  # type: ignore[arg-type]


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create a configured FastAPI application with isolated database resources."""
    runtime_settings = settings or get_settings()
    engine = create_database_engine(runtime_settings)
    session_factory = create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        migrate_schema(engine)
        if runtime_settings.seed_on_startup:
            seed_default_admin(session_factory)
        yield
        engine.dispose()

    app = FastAPI(title="WriteSpace API", version="0.1.0", description="Safe WriteSpace API.", lifespan=lifespan)
    app.state.engine = engine
    app.state.session_factory = session_factory

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next: object) -> object:
        request.state.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response = await call_next(request)  # type: ignore[operator]
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message, "request_id": request_id}, headers={"X-Request-ID": request_id})

    app.add_middleware(CORSMiddleware, allow_origins=runtime_settings.allowed_origins, allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type", "X-Request-ID"])
    for router in (health_router, public_router, auth_router, posts_router, admin_router, users_router):
        app.include_router(router)
    return app


app = create_app()
