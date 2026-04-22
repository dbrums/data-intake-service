from uuid import UUID

from app.domains.job import Job
from app.repositories.job_repository import AbstractJobRepository


class FakeJobRepository(AbstractJobRepository):
    def __init__(self) -> None:
        self._jobs: dict[UUID, Job] = {}

    def create(self, job: Job) -> Job:
        self._jobs[job.id] = job
        return job

    def get_by_id(self, job_id: UUID) -> Job | None:
        return self._jobs.get(job_id)

    def list_all(self) -> list[Job]:
        return list(self._jobs.values())
