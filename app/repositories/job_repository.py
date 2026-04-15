from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.job import Job


class JobRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, job: Job) -> Job:
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return job

    def get_by_id(self, job_id: UUID) -> Job | None:
        return self._session.get(Job, job_id)
