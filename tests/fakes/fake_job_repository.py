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

    def get_by_idempotency_key(self, idempotency_key: str) -> Job | None:
        for job in self._jobs.values():
            if job.idempotency_key == idempotency_key:
                return job
        return None

    def list_all(self) -> list[Job]:
        return list(self._jobs.values())

    def update(self, job: Job) -> Job:
        self._jobs[job.id] = job
        return job
