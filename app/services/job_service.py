from app.db.models.job import Job
from app.repositories.job_repository import AbstractJobRepository
from app.schemas.job import JobCreate


class JobService:
    def __init__(self, repo: AbstractJobRepository):
        self._repo = repo

    def create_job(self, payload: JobCreate) -> Job:
        job = Job(
            dataset_type=payload.dataset_type,
            schema_version=payload.schema_version,
            source_type=payload.source_type,
            source_uri=payload.source_uri,
            status="queued",
        )
        return self._repo.create(job)
