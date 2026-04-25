from uuid import uuid4

import pytest

from app.domains.job import JobStatus
from app.schemas.job import JobCreate
from app.services.job_service import JobNotFoundError, JobService
from tests.factories.job_factory import DEFAULTS
from tests.fakes.fake_job_repository import FakeJobRepository


def test_job_service_create_job(
    fake_job_repo: FakeJobRepository, job_create: JobCreate
):
    service = JobService(fake_job_repo)
    job = service.create_job(job_create)

    assert job.id is not None
    assert job.status == JobStatus.QUEUED
    attr_list = [
        "dataset_type",
        "schema_version",
        "source_type",
        "source_uri",
    ]
    for field in attr_list:
        assert getattr(job, field) == DEFAULTS.get(field)


def test_job_service_get_jobs_returns_empty_list(fake_job_repo: FakeJobRepository):
    service = JobService(fake_job_repo)
    jobs = service.get_jobs()

    assert jobs == []


def test_job_service_get_jobs_returns_single_job(
    fake_job_repo: FakeJobRepository, job_create: JobCreate
):
    service = JobService(fake_job_repo)
    created_job = service.create_job(job_create)

    jobs = service.get_jobs()

    assert len(jobs) == 1
    assert jobs[0].id == created_job.id
    assert jobs[0].status == JobStatus.QUEUED


def test_job_service_get_jobs_returns_multiple_jobs(
    fake_job_repo: FakeJobRepository, job_create: JobCreate
):
    service = JobService(fake_job_repo)
    created_job1 = service.create_job(job_create)
    created_job2 = service.create_job(job_create)
    created_job3 = service.create_job(job_create)

    jobs = service.get_jobs()

    assert len(jobs) == 3
    job_ids = [job.id for job in jobs]
    assert created_job1.id in job_ids
    assert created_job2.id in job_ids
    assert created_job3.id in job_ids


def test_job_service_start_job(fake_job_repo: FakeJobRepository, job_create: JobCreate):
    service = JobService(fake_job_repo)
    job = service.create_job(job_create)

    started_job = service.start_job(job.id)

    assert job.id == started_job.id
    assert started_job.status == JobStatus.RUNNING


def test_job_service_start_job_nonexistent_job(fake_job_repo: FakeJobRepository):
    service = JobService(fake_job_repo)
    with pytest.raises(JobNotFoundError):
        service.start_job(uuid4())


def test_job_service_complete_job(
    fake_job_repo: FakeJobRepository, job_create: JobCreate
):
    service = JobService(fake_job_repo)
    job = service.create_job(job_create)

    started_job = service.start_job(job.id)
    completed_job = service.complete_job(started_job.id)

    assert started_job.id == completed_job.id
    assert completed_job.status == JobStatus.SUCCEEDED


def test_job_service_complete_job_nonexistent_job(fake_job_repo: FakeJobRepository):
    service = JobService(fake_job_repo)
    with pytest.raises(JobNotFoundError):
        service.complete_job(uuid4())
