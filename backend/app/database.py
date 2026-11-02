"""Database engine and session management."""
import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

log = logging.getLogger(__name__)

SQLITE_URL = f"sqlite:///{Path(__file__).resolve().parent.parent / 'mlimismart.db'}"


class Base(DeclarativeBase):
    pass


def _build_engine():
    """Try MySQL first; fall back to SQLite only if allowed."""
    url = settings.database_url
    try:
        engine = create_engine(url, pool_pre_ping=True, future=True)
        with engine.connect():
            pass
        log.info("Connected to database: %s", url.split("@")[-1])
        return engine, url
    except Exception as exc:  # noqa: BLE001 - any driver error is a fallback trigger
        if not settings.allow_sqlite_fallback:
            raise
        log.warning(
            "Could not connect to MySQL (%s). Falling back to SQLite at %s. "
            "Start WAMP and create the 'mlimismart' database to use MySQL.",
            exc.__class__.__name__,
            SQLITE_URL,
        )
        engine = create_engine(
            SQLITE_URL, connect_args={"check_same_thread": False}, future=True
        )
        return engine, SQLITE_URL


engine, active_database_url = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401 - registers the mappings

    Base.metadata.create_all(bind=engine)
