from uuid import UUID, uuid4

from app.db.models.job import Job
from app.repositories.job_repository import AbstractJobRepository


class FakeJobRepository(AbstractJobRepository):
    def __init__(self) -> None:
        self._jobs: dict[UUID, Job] = {}

    def create(self, job: Job) -> Job:
        job.id = uuid4()
        self._jobs[job.id] = job
        return job

    def get_by_id(self, job_id: UUID) -> Job | None:
        return self._jobs.get(job_id)
