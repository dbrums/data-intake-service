from app.domains.job import DataSource, Job
from app.repositories.job_repository import AbstractJobRepository
from app.schemas.job import JobCreate


class JobService:
    def __init__(self, repo: AbstractJobRepository):
        self._repo = repo

    def create_job(self, payload: JobCreate) -> Job:

        data_source = DataSource(
            type=payload.source_type,
            uri=payload.source_uri,
        )
        in_job = Job.create_new(
            dataset_type=payload.dataset_type,
            schema_version=payload.schema_version,
            source=data_source,
        )
        return self._repo.create(in_job)
