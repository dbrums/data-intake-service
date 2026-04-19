"""Shared FastAPI dependencies (database sessions, auth, etc.)."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_session


def get_db() -> Generator[Session]:
    """FastAPI dependency that provides a database session."""
    yield from get_session()
