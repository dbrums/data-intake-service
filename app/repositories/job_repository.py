from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.job import Job as DBJob
from app.domains.job import Job


class AbstractJobRepository(ABC):
    @abstractmethod
    def create(self, job: Job) -> Job:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, job_id: UUID) -> Job | None:
        raise NotImplementedError


class SqlAlchemyJobRepository(AbstractJobRepository):
    def __init__(self, session: Session):
        self._session = session

    def create(self, job: Job) -> Job:
        db_job = Job.to_db_model(job)
        self._session.add(db_job)
        self._session.commit()
        self._session.refresh(db_job)
        return Job.from_db_model(db_job)

    def get_by_id(self, job_id: UUID) -> Job | None:
        db_job = self._session.get(DBJob, job_id)
        return None if db_job is None else Job.from_db_model(db_job)
