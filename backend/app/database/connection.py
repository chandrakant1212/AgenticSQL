"""
Database connection management.

Provides two engine configurations:
- Admin engine: for DDL, seeding, and migrations
- Read-only engine: for query execution (enforces statement timeout)
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine singletons
# ---------------------------------------------------------------------------

_admin_engine: Engine | None = None
_readonly_engine: Engine | None = None


def get_admin_engine() -> Engine:
    """Get or create the admin database engine (for DDL and seeding)."""
    global _admin_engine
    if _admin_engine is None:
        settings = get_settings()
        _admin_engine = create_engine(
            settings.DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False,
        )
        logger.info("Admin database engine created")
    return _admin_engine


def get_readonly_engine() -> Engine:
    """Get or create the read-only database engine (for query execution)."""
    global _readonly_engine
    if _readonly_engine is None:
        settings = get_settings()

        # Use admin URL as fallback if readonly not separately configured
        readonly_url = settings.DATABASE_URL_READONLY or settings.DATABASE_URL
        _readonly_engine = create_engine(
            readonly_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False,
        )

        # Enforce statement timeout on every connection checkout
        timeout_ms = settings.QUERY_TIMEOUT_SECONDS * 1000

        @event.listens_for(_readonly_engine, "connect")
        def set_timeout(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute(f"SET statement_timeout = {timeout_ms}")
            cursor.close()

        logger.info(
            "Read-only database engine created (timeout=%ds)",
            settings.QUERY_TIMEOUT_SECONDS,
        )
    return _readonly_engine


# ---------------------------------------------------------------------------
# Session factories
# ---------------------------------------------------------------------------

def get_admin_session_factory() -> sessionmaker:
    """Get session factory for admin operations."""
    return sessionmaker(bind=get_admin_engine(), expire_on_commit=False)


def get_readonly_session_factory() -> sessionmaker:
    """Get session factory for read-only operations."""
    return sessionmaker(bind=get_readonly_engine(), expire_on_commit=False)


# ---------------------------------------------------------------------------
# Context managers
# ---------------------------------------------------------------------------

@contextmanager
def admin_session() -> Generator[Session, None, None]:
    """Context manager for admin database sessions."""
    factory = get_admin_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def readonly_session() -> Generator[Session, None, None]:
    """Context manager for read-only database sessions."""
    factory = get_readonly_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def check_database_health() -> dict:
    """Check if the database is reachable."""
    try:
        engine = get_admin_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "message": "Database connection successful"}
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        return {"status": "unhealthy", "message": str(e)}


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def dispose_engines() -> None:
    """Dispose all database engines. Call on application shutdown."""
    global _admin_engine, _readonly_engine
    if _admin_engine:
        _admin_engine.dispose()
        _admin_engine = None
    if _readonly_engine:
        _readonly_engine.dispose()
        _readonly_engine = None
    logger.info("Database engines disposed")
