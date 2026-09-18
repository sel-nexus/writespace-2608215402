"""SQLAlchemy database setup for file-backed SQLite persistence."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import Settings


class Base(DeclarativeBase):
    """Base class for WriteSpace ORM models."""


def ensure_sqlite_parent(database_url: str) -> None:
    """Create the parent directory for a file-backed SQLite database URL."""
    url = make_url(database_url)
    if url.drivername.startswith("sqlite") and url.database and url.database != ":memory:":
        Path(url.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def create_database_engine(settings: Settings) -> Engine:
    """Create a SQLite engine with foreign-key enforcement enabled."""
    ensure_sqlite_parent(settings.database_url)
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection: object, _: object) -> None:
        """Enable SQLite foreign keys for every physical database connection."""
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Build a session factory bound to the supplied engine."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Yield and reliably close a SQLAlchemy session."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
