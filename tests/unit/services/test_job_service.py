from collections.abc import Callable
from uuid import UUID, uuid4

import pytest

from app.core.config import settings
from app.domains.job import JobStatus
from app.schemas.job import JobCreate, JobFail
from app.services.job_service import (
    IdempotencyKeyConflictError,
    IdempotentCreateInTerminalStateError,
    JobNotFoundError,
    JobService,
    MaxRetriesExceededError,
)
from tests.factories.job_factory import DEFAULTS
from tests.fakes.fake_job_repository import FakeJobRepository


@pytest.fixture
def job_in_status(
    fake_job_repo: FakeJobRepository,
    job_create: Callable[..., JobCreate],
    job_fail: JobFail,
) -> Callable[[JobStatus], UUID]:
    def _create_job(status: JobStatus) -> UUID:
        service = JobService(fake_job_repo)
        created_job = service.create_job(job_create())
        job_id = created_job.id

        if status == JobStatus.RUNNING:
            service.start_job(job_id)
        elif status == JobStatus.FAILED:
            service.start_job(job_id)
            service.fail_job(job_fail, job_id)

        return job_id

    return _create_job


def test_job_service_create_job(
    fake_job_repo: FakeJobRepository, job_create: Callable[..., JobCreate]
):
    service = JobService(fake_job_repo)
    job = service.create_job(job_create())

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
    assert job.created_at is not None


def test_job_service_get_jobs_returns_empty_list(fake_job_repo: FakeJobRepository):
    service = JobService(fake_job_repo)
    jobs = service.get_jobs()

    assert jobs == []


def test_job_service_get_jobs_returns_single_job(
    fake_job_repo: FakeJobRepository, job_create: Callable[..., JobCreate]
):
    service = JobService(fake_job_repo)
    created_job = service.create_job(job_create())

    jobs = service.get_jobs()

    assert len(jobs) == 1
    assert jobs[0].id == created_job.id
    assert jobs[0].status == JobStatus.QUEUED


def test_job_service_get_jobs_returns_multiple_jobs(
    fake_job_repo: FakeJobRepository, job_create: Callable[..., JobCreate]
):
    service = JobService(fake_job_repo)
    created_job1 = service.create_job(job_create())
    created_job2 = service.create_job(job_create())
    created_job3 = service.create_job(job_create())

    jobs = service.get_jobs()

    assert len(jobs) == 3
    job_ids = [job.id for job in jobs]
    assert created_job1.id in job_ids
    assert created_job2.id in job_ids
    assert created_job3.id in job_ids


def test_job_service_start_job(
    fake_job_repo: FakeJobRepository, job_create: Callable[..., JobCreate]
):
    service = JobService(fake_job_repo)
    job = service.create_job(job_create())

    started_job = service.start_job(job.id)

    assert job.id == started_job.id
    assert started_job.status == JobStatus.RUNNING
    assert started_job.created_at is not None
    assert started_job.started_at is not None
    assert started_job.finished_at is None
    assert started_job.created_at <= started_job.started_at


def test_job_service_start_job_nonexistent_job(fake_job_repo: FakeJobRepository):
    service = JobService(fake_job_repo)
    with pytest.raises(JobNotFoundError):
        service.start_job(uuid4())


def test_job_service_complete_job(
    fake_job_repo: FakeJobRepository, job_create: Callable[..., JobCreate]
):
    service = JobService(fake_job_repo)
    job = service.create_job(job_create())

    started_job = service.start_job(job.id)
    completed_job = service.complete_job(started_job.id)

    assert started_job.id == completed_job.id
    assert completed_job.status == JobStatus.SUCCEEDED
    assert completed_job.started_at is not None
    assert completed_job.finished_at is not None
    assert completed_job.started_at <= completed_job.finished_at


def test_job_service_complete_job_nonexistent_job(fake_job_repo: FakeJobRepository):
    service = JobService(fake_job_repo)
    with pytest.raises(JobNotFoundError):
        service.complete_job(uuid4())


def test_job_service_fail_job(
    fake_job_repo: FakeJobRepository,
    job_create: Callable[..., JobCreate],
    job_fail: JobFail,
):
    service = JobService(fake_job_repo)
    job = service.create_job(job_create())

    started_job = service.start_job(job.id)
    failed_job = service.fail_job(job_fail, started_job.id)

    assert started_job.id == failed_job.id
    assert failed_job.status == JobStatus.FAILED
    assert failed_job.error_code == job_fail.error_code
    assert failed_job.error_message == job_fail.error_message
    assert failed_job.started_at is not None
    assert failed_job.finished_at is not None
    assert failed_job.started_at <= failed_job.finished_at


def test_job_service_fail_job_nonexistent_job(
    fake_job_repo: FakeJobRepository, job_fail: JobFail
):
    service = JobService(fake_job_repo)
    with pytest.raises(JobNotFoundError):
        service.fail_job(job_fail, uuid4())


def test_job_service_retry_job(
    fake_job_repo: FakeJobRepository,
    job_create: Callable[..., JobCreate],
    job_fail: JobFail,
):
    service = JobService(fake_job_repo)
    job = service.create_job(job_create())

    for i in range(settings.MAX_JOB_RETRIES):
        service.start_job(job.id)
        failed_job = service.fail_job(job_fail, job.id)
        retried_job = service.retry_job(failed_job.id)
        assert failed_job.id == retried_job.id
        assert retried_job.status == JobStatus.QUEUED
        assert retried_job.retry_count == i + 1
        assert retried_job.started_at is None
        assert retried_job.finished_at is None

    service.start_job(job.id)
    failed_job = service.fail_job(job_fail, job.id)
    with pytest.raises(MaxRetriesExceededError):
        service.retry_job(failed_job.id)


def test_job_service_retry_job_nonexistent_job(fake_job_repo: FakeJobRepository):
    service = JobService(fake_job_repo)
    with pytest.raises(JobNotFoundError):
        service.retry_job(uuid4())


@pytest.mark.parametrize(
    "status",
    [JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.FAILED, JobStatus.RETRY_SCHEDULED],
)
def test_job_service_cancel_job(
    fake_job_repo: FakeJobRepository,
    job_in_status: Callable[[JobStatus], UUID],
    status: JobStatus,
):
    job_id = job_in_status(status)
    service = JobService(fake_job_repo)
    cancelled_job = service.cancel_job(job_id)

    assert cancelled_job.status == JobStatus.CANCELLED
    assert cancelled_job.finished_at is not None


def test_job_service_cancel_job_nonexistent_job(fake_job_repo: FakeJobRepository):
    service = JobService(fake_job_repo)
    with pytest.raises(JobNotFoundError):
        service.cancel_job(uuid4())


def test_job_service_create_job_with_idempotency_key_returns_same_job(
    fake_job_repo: FakeJobRepository, job_create: Callable[..., JobCreate]
):
    service = JobService(fake_job_repo)
    payload = job_create(idempotency_key="test-key")

    job1 = service.create_job(payload)
    job2 = service.create_job(payload)

    assert job1.id == job2.id
    assert job1.idempotency_key == "test-key"


def test_job_service_create_job_with_idempotency_key_different_params_raises(
    fake_job_repo: FakeJobRepository, job_create: Callable[..., JobCreate]
):
    service = JobService(fake_job_repo)
    payload1 = job_create(idempotency_key="test-key", dataset_type="type1")
    payload2 = job_create(idempotency_key="test-key", dataset_type="type2")

    service.create_job(payload1)

    with pytest.raises(IdempotencyKeyConflictError, match="different parameters"):
        service.create_job(payload2)


def test_job_service_create_job_with_idempotency_key_terminal_state_raises(
    fake_job_repo: FakeJobRepository, job_create: Callable[..., JobCreate]
):
    service = JobService(fake_job_repo)
    payload = job_create(idempotency_key="test-key")

    job = service.create_job(payload)
    service.start_job(job.id)
    service.complete_job(job.id)

    with pytest.raises(IdempotentCreateInTerminalStateError, match="cannot be retried"):
        service.create_job(payload)
