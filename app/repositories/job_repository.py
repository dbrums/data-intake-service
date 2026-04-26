import logging
from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, MultipleResultsFound, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.job import Job as DBJob
from app.domains.job import IdempotencyKeyIntegrityError, Job

logger = logging.getLogger(__name__)


class AbstractJobRepository(ABC):
    @abstractmethod
    def create(self, job: Job) -> Job:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, job_id: UUID) -> Job | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_idempotency_key(self, idempotency_key: str) -> Job | None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Job]:
        raise NotImplementedError

    @abstractmethod
    def update(self, job: Job) -> Job:
        raise NotImplementedError


class SqlAlchemyJobRepository(AbstractJobRepository):
    def __init__(self, session: Session):
        self._session = session

    def create(self, job: Job) -> Job:
        try:
            db_job = Job.to_db_model(job)
            self._session.add(db_job)
            self._session.commit()
            self._session.refresh(db_job)
            return Job.from_db_model(db_job)
        except IntegrityError as e:
            self._session.rollback()
            # Check if it's the idempotency key constraint violation
            if job.idempotency_key and "idempotency_key" in str(e.orig).lower():
                logger.info(
                    f"idempotency key constraint violation: {job.idempotency_key}"
                )
                # Race condition - return existing job
                existing = self.get_by_idempotency_key(job.idempotency_key)
                if existing:
                    return existing
            # Re-raise if it's a different integrity error or job not found
            logger.error("database integrity error during job creation", exc_info=True)
            raise
        except SQLAlchemyError:
            logger.error("database error during job creation", exc_info=True)
            self._session.rollback()
            raise

    def get_by_id(self, job_id: UUID) -> Job | None:
        try:
            db_job = self._session.get(DBJob, job_id)
            return None if db_job is None else Job.from_db_model(db_job)
        except SQLAlchemyError:
            logger.error("database error during job retrieval", exc_info=True)
            raise

    def get_by_idempotency_key(self, idempotency_key: str) -> Job | None:
        try:
            query = select(DBJob).where(DBJob.idempotency_key == idempotency_key)
            db_job = self._session.scalars(query).one_or_none()
            return None if db_job is None else Job.from_db_model(db_job)
        except MultipleResultsFound as e:
            logger.error(
                f"multiple results found for idempotency key {idempotency_key}"
            )
            raise IdempotencyKeyIntegrityError(
                "Database integrity violation: duplicate idempotency keys found"
            ) from e
        except SQLAlchemyError:
            logger.error("database error during job retrieval", exc_info=True)
            raise

    def list_all(self) -> list[Job]:
        try:
            db_jobs = self._session.query(DBJob).all()
            return [Job.from_db_model(db_job) for db_job in db_jobs]
        except SQLAlchemyError:
            logger.error("database error during job listing", exc_info=True)
            raise

    def update(self, job: Job) -> Job:
        try:
            db_job = self._session.get(DBJob, job.id)
            if db_job is None:
                raise ValueError(f"Job with id {job.id} not found")

            db_job.status = job.status.value  # Convert enum to string
            db_job.started_at = job.started_at
            db_job.finished_at = job.finished_at
            db_job.error_code = job.error_code
            db_job.error_message = job.error_message
            db_job.retry_count = job.retry_count
            self._session.commit()
            self._session.refresh(db_job)
            return Job.from_db_model(db_job)
        except SQLAlchemyError:
            logger.error("database error during job update", exc_info=True)
            self._session.rollback()
            raise
