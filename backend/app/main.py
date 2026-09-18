"""FastAPI application factory and restart-safe database initialization."""

import logging
import uuid
from collections.abc import AsyncIterator

from fastapi import Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.errors import DomainError
from app.database import Base, create_database_engine, create_session_factory
from app.models import User
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.public import router as public_router

logger = logging.getLogger(__name__)


def seed_default_admin(session_factory: sessionmaker[Session]) -> None:
    """Idempotently create only the default bcrypt-hashed development admin."""
    session = session_factory()
    try:
        existing = session.scalar(select(User).where(User.username == "admin"))
        if existing is None:
            password_hash = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode("utf-8")
            session.add(User(display_name="Admin", username="admin", password_hash=password_hash, role="admin", is_default=True, is_active=True))
            session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logger.warning("Default admin seed failed: %s", exc.__class__.__name__)
    finally:
        session.close()


def upgrade_user_schema(engine: object) -> None:
    """Add authentication user columns to a fresh-project SQLite database safely.

    Args:
        engine: SQLAlchemy engine owning the SQLite schema.
    """
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    additions = {
        "display_name": "VARCHAR(120) NOT NULL DEFAULT 'Admin'",
        "role": "VARCHAR(20) NOT NULL DEFAULT 'user'",
        "is_default": "BOOLEAN NOT NULL DEFAULT 0",
        "is_active": "BOOLEAN NOT NULL DEFAULT 1",
        "created_at": "DATETIME",
    }
    with engine.begin() as connection:  # type: ignore[attr-defined]
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {definition}"))
        connection.execute(text("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create a configured FastAPI application with its own database resources."""
    runtime_settings = settings or get_settings()
    engine = create_database_engine(runtime_settings)
    session_factory = create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        """Create SQLite schema and run the restart-safe seed before serving."""
        Base.metadata.create_all(engine)
        upgrade_user_schema(engine)
        if runtime_settings.seed_on_startup:
            seed_default_admin(session_factory)
        yield
        engine.dispose()

    app = FastAPI(
        title="WriteSpace API",
        version="0.1.0",
        description="Safe public reading endpoints for WriteSpace.",
        lifespan=lifespan,
    )
    app.state.engine = engine
    app.state.session_factory = session_factory

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next: object) -> object:
        """Attach a stable request ID to every response."""
        request.state.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response = await call_next(request)  # type: ignore[operator]
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        """Return a safe request-ID envelope for known domain failures."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message, "request_id": request_id}, headers={"X-Request-ID": request_id})
    app.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    app.include_router(health_router)
    app.include_router(public_router)
    app.include_router(auth_router)
    return app


app = create_app()
