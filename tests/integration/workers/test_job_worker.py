"""Integration tests for worker job processing.

NOTE: These tests require a real database (not SQLite in-memory) because the worker
runs in a separate session and needs to see committed data. Set TEST_DATABASE_URL
to use PostgreSQL or SQLite file database:

    TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/data_intake pytest
    TEST_DATABASE_URL=sqlite:///./test_worker.db pytest

These tests also require Redis to be running on localhost:6379.
"""

import os
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from redis import Redis, RedisError
from rq import Queue, SimpleWorker
from sqlalchemy.orm import Session

from app.domains.job import JobStatus
from app.repositories.job_repository import SqlAlchemyJobRepository
from app.schemas.job import JobCreate
from app.services.job_service import JobService
from app.workers.tasks import execute_validation_job

# Skip all tests in this module if using in-memory database or no Redis
_TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
_SKIP_REASON = (
    "Worker integration tests require a real database (not in-memory SQLite). "
    "Set TEST_DATABASE_URL to postgresql://... or sqlite:///file.db"
)

pytestmark = pytest.mark.skipif(
    _TEST_DB_URL == "sqlite:///:memory:",
    reason=_SKIP_REASON,
)


@pytest.fixture
def redis_conn():
    """Create Redis connection for tests."""
    # Use DB 1 for tests to avoid conflicts with development
    # Local Redis typically has no password, Docker Redis has password
    try:
        redis = Redis(host="localhost", port=6379, db=1, decode_responses=True)
        redis.ping()  # type: ignore[no-untyped-call]
    except Exception:
        try:
            # If that fails, it might be in Docker with password
            redis = Redis(
                host="localhost",
                port=6379,
                db=1,
                password="redis",
                decode_responses=True,
            )
            redis.ping()  # type: ignore[no-untyped-call]
        except (RedisError, Exception) as e:
            pytest.skip(f"Redis not available: {e}")
    redis.flushdb()  # type: ignore[no-untyped-call]
    yield redis
    redis.flushdb()  # type: ignore[no-untyped-call]
    redis.close()


@pytest.fixture
def test_queue(redis_conn: Redis):
    """Create test queue."""
    return Queue("test", connection=redis_conn, is_async=False)


class TestJobWorkerIntegration:
    """Integration tests for worker processing jobs end-to-end."""

    @patch("app.workers.tasks.sleep")  # Mock sleep to speed up tests
    def test_worker_processes_job_successfully(
        self,
        mock_sleep,  # type: ignore[misc]
        db_session: Session,
        redis_conn: Redis,
        test_queue: Queue,
    ):
        """Test that worker picks up job and processes it through to completion."""
        # Arrange
        repo = SqlAlchemyJobRepository(db_session)
        service = JobService(repo)

        # Create a job in the database
        job_create = JobCreate(
            dataset_type="test_data",
            schema_version="1.0",
            source_type="url",
            source_uri="https://example.com/test.csv",
        )
        job = service.create_job(job_create)

        # Commit so worker can see the job in its own session
        db_session.commit()

        assert job.status == JobStatus.QUEUED

        # Enqueue the job manually (bypass service.create_job's enqueue)
        test_queue.enqueue(execute_validation_job, job.id)  # type: ignore[call-arg]

        # Act - Process the queue synchronously
        worker = SimpleWorker([test_queue], connection=redis_conn)
        worker.work(burst=True, max_jobs=1)

        # Assert - Verify job transitioned through states
        db_session.expire_all()  # Refresh from database
        completed_job = repo.get_by_id(job.id)

        assert completed_job is not None
        assert completed_job.status == JobStatus.SUCCEEDED
        assert completed_job.started_at is not None
        assert completed_job.finished_at is not None
        assert completed_job.error_code is None
        assert completed_job.error_message is None

    @patch("app.workers.tasks.sleep")
    def test_worker_handles_job_failure(
        self,
        mock_sleep,  # type: ignore[misc]
        db_session: Session,
        redis_conn: Redis,
        test_queue: Queue,
    ):
        """Test that worker handles job failures and marks job as FAILED."""
        # Arrange
        repo = SqlAlchemyJobRepository(db_session)
        service = JobService(repo)

        job_create = JobCreate(
            dataset_type="test_data",
            schema_version="1.0",
            source_type="url",
            source_uri="https://example.com/test.csv",
        )
        job = service.create_job(job_create)
        db_session.commit()

        # Make the validation fail
        mock_sleep.side_effect = Exception("Test validation failure")

        test_queue.enqueue(execute_validation_job, job.id)  # type: ignore[call-arg]

        # Act - Process the queue
        worker = SimpleWorker([test_queue], connection=redis_conn)
        worker.work(burst=True, max_jobs=1)

        # Assert - Job should be marked as FAILED
        db_session.expire_all()
        failed_job = repo.get_by_id(job.id)

        assert failed_job is not None
        assert failed_job.status == JobStatus.FAILED
        assert failed_job.started_at is not None
        assert failed_job.finished_at is not None
        assert failed_job.error_code == "WORKER_ERROR"
        assert (
            failed_job.error_message
            and "Test validation failure" in failed_job.error_message
        )

    def test_multiple_jobs_processed_sequentially(
        self,
        db_session: Session,
        redis_conn: Redis,
        test_queue: Queue,
    ):
        """Test that worker processes multiple jobs in order."""
        # Arrange
        repo = SqlAlchemyJobRepository(db_session)
        service = JobService(repo)

        # Create 3 jobs
        job_ids: list[UUID] = []
        for i in range(3):
            job_create = JobCreate(
                dataset_type=f"test_data_{i}",
                schema_version="1.0",
                source_type="url",
                source_uri=f"https://example.com/test{i}.csv",
            )
            job = service.create_job(job_create)
            job_ids.append(job.id)
            test_queue.enqueue(execute_validation_job, job.id)  # type: ignore[call-arg]

        db_session.commit()

        # Act - Process all jobs with mocked sleep for speed
        with patch("app.workers.tasks.sleep"):
            worker = SimpleWorker([test_queue], connection=redis_conn)
            worker.work(burst=True)

        # Assert - All jobs completed
        db_session.expire_all()
        for job_id in job_ids:
            completed_job = repo.get_by_id(job_id)
            assert completed_job is not None
            assert completed_job.status == JobStatus.SUCCEEDED

    def test_job_transitions_through_correct_states(
        self,
        db_session: Session,
        redis_conn: Redis,
        test_queue: Queue,
    ):
        """Test that job transitions QUEUED → RUNNING → SUCCEEDED."""
        # Arrange
        repo = SqlAlchemyJobRepository(db_session)
        service = JobService(repo)

        job_create = JobCreate(
            dataset_type="test_data",
            schema_version="1.0",
            source_type="url",
            source_uri="https://example.com/test.csv",
        )
        job = service.create_job(job_create)
        initial_status = job.status

        db_session.commit()
        test_queue.enqueue(execute_validation_job, job.id)  # type: ignore[call-arg]

        # Act
        with patch("app.workers.tasks.sleep"):
            worker = SimpleWorker([test_queue], connection=redis_conn)
            worker.work(burst=True, max_jobs=1)

        # Assert state transitions
        db_session.expire_all()
        final_job = repo.get_by_id(job.id)

        assert initial_status == JobStatus.QUEUED
        assert final_job is not None
        assert final_job.status == JobStatus.SUCCEEDED

        # Verify timestamps are set correctly
        assert final_job.created_at is not None
        assert final_job.started_at is not None
        assert final_job.finished_at is not None
        assert final_job.created_at < final_job.started_at
        assert final_job.started_at < final_job.finished_at

    @patch("app.workers.tasks.sleep")
    def test_worker_with_nonexistent_job_id(
        self,
        mock_sleep,  # type: ignore[misc]
        db_session: Session,
        redis_conn: Redis,
        test_queue: Queue,
    ):
        """Test worker behavior when job ID doesn't exist in database."""
        # Arrange - Enqueue a job with non-existent ID
        fake_job_id = uuid4()
        test_queue.enqueue(execute_validation_job, fake_job_id)  # type: ignore[call-arg]

        # Act - Worker should fail when trying to fetch the job
        worker = SimpleWorker([test_queue], connection=redis_conn)
        worker.work(burst=True, max_jobs=1)

        # Assert - Job should fail (RQ will mark it as failed)
        # We can't verify job state in DB since it doesn't exist
        # But we can verify the queue is empty after processing
        assert test_queue.count == 0
