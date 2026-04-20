"""Shared FastAPI dependencies (database sessions, auth, etc.)."""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.repositories.job_repository import (
    AbstractJobRepository,
    SqlAlchemyJobRepository,
)
from app.services.job_service import JobService


def get_db() -> Generator[Session]:
    """FastAPI dependency that provides a database session."""
    yield from get_session()


def get_job_repository(db: Session = Depends(get_db)) -> AbstractJobRepository:
    return SqlAlchemyJobRepository(db)


def get_job_service(
    repo: AbstractJobRepository = Depends(get_job_repository),
) -> JobService:
    return JobService(repo)
