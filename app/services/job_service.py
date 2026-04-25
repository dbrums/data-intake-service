import datetime
import logging
from uuid import UUID

from app.core.logging import set_job_id
from app.domains.job import DataSource, Job, JobStatus
from app.repositories.job_repository import AbstractJobRepository
from app.schemas.job import JobCreate, JobFail

logger = logging.getLogger(__name__)


class JobNotFoundError(Exception):
    pass


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
        set_job_id(in_job.id)
        logger.info(
            "creating job",
            extra={
                "dataset_type": payload.dataset_type,
                "source_type": payload.source_type,
            },
        )
        job = self._repo.create(in_job)
        logger.info("job created successfully")
        return job

    def get_job_by_id(self, job_id: UUID) -> Job:
        set_job_id(job_id)
        logger.info("fetching job")
        job = self._repo.get_by_id(job_id)
        if job is None:
            logger.warning("job not found")
            raise JobNotFoundError(f"No job found with ID {job_id}")
        logger.info("job retrieved successfully")
        return job

    def get_jobs(self) -> list[Job]:
        logger.info("fetching all jobs")
        jobs = self._repo.list_all()
        logger.info("jobs retrieved successfully")
        return jobs

    def start_job(self, job_id: UUID) -> Job:
        set_job_id(job_id)
        logger.info("starting job")
        job = self.get_job_by_id(job_id)
        job.transition_to(JobStatus.RUNNING)
        job.started_at = datetime.datetime.now(datetime.UTC)
        updated_job = self._repo.update(job)
        logger.info("job started successfully")
        return updated_job

    def complete_job(self, job_id: UUID) -> Job:
        set_job_id(job_id)
        logger.info("completing job")
        job = self.get_job_by_id(job_id)
        job.transition_to(JobStatus.SUCCEEDED)
        job.finished_at = datetime.datetime.now(datetime.UTC)
        updated_job = self._repo.update(job)
        logger.info("job completed successfully")
        return updated_job

    def fail_job(self, payload: JobFail, job_id: UUID) -> Job:
        set_job_id(job_id)
        logger.info("failing job")
        job = self.get_job_by_id(job_id)
        job.transition_to(JobStatus.FAILED)
        job.error_code = payload.error_code
        job.error_message = payload.error_message
        updated_job = self._repo.update(job)
        logger.info("job failed successfully")
        return updated_job
