"""FastAPI application factory and restart-safe database initialization."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.database import Base, create_database_engine, create_session_factory
from app.models import User
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
            session.add(User(username="admin", password_hash=password_hash))
            session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logger.warning("Default admin seed failed: %s", exc.__class__.__name__)
    finally:
        session.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create a configured FastAPI application with its own database resources."""
    runtime_settings = settings or get_settings()
    engine = create_database_engine(runtime_settings)
    session_factory = create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        """Create SQLite schema and run the restart-safe seed before serving."""
        Base.metadata.create_all(engine)
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Content-Type"],
    )
    app.include_router(health_router)
    app.include_router(public_router)
    return app


app = create_app()
