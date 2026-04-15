"""Database session factory.

Used by both API dependencies and background workers.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  # set True temporarily if you want to see SQL in logs
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_session() -> Generator[Session, None, None]:
    """Yield a database session and ensure it is closed after use."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
