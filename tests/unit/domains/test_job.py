from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.db.models.job import Job as DBJob
from app.domains.job import DataSource, InvalidJobTransitionError, Job, JobStatus
from tests.factories.job_factory import DEFAULTS, job_factory


# Fixtures
@pytest.fixture
def url_data_source() -> DataSource:
    return DataSource(type="url", uri="https://example.com/data.csv")


@pytest.fixture
def upload_data_source() -> DataSource:
    return DataSource(type="upload", uri="s3://bucket/file.csv")


class TestDataSource:
    """Tests for DataSource value object"""

    @pytest.mark.parametrize(
        "source_type,uri",
        [
            ("url", "https://example.com/data.csv"),
            ("upload", "s3://bucket/file.csv"),
        ],
    )
    def test_create_data_source(self, source_type: str, uri: str) -> None:
        source = DataSource(type=source_type, uri=uri)

        assert source.type == source_type
        assert source.uri == uri

    def test_invalid_source_type_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid source type: ftp"):
            DataSource(type="ftp", uri="ftp://example.com/data.csv")

    def test_data_source_equality(self, url_data_source: DataSource) -> None:
        source1 = url_data_source
        source2 = DataSource(type="url", uri="https://example.com/data.csv")

        assert source1 == source2


class TestJobStatus:
    """Tests for JobStatus enum"""

    @pytest.mark.parametrize(
        "status,expected_value",
        [
            (JobStatus.QUEUED, "queued"),
            (JobStatus.RUNNING, "running"),
            (JobStatus.SUCCEEDED, "succeeded"),
            (JobStatus.FAILED, "failed"),
            (JobStatus.CANCELLED, "cancelled"),
            (JobStatus.RETRY_SCHEDULED, "retry_scheduled"),
        ],
    )
    def test_status_values(self, status: JobStatus, expected_value: str) -> None:
        assert status == expected_value

    def test_status_from_string(self) -> None:
        status = JobStatus("queued")
        assert status == JobStatus.QUEUED

    def test_invalid_status_raises_error(self) -> None:
        with pytest.raises(ValueError):
            JobStatus("invalid")


class TestJobCreateNew:
    """Tests for Job.create_new factory method"""

    def test_create_job(self, url_data_source: DataSource) -> None:
        job = Job.create_new(
            dataset_type="sales",
            schema_version="v2",
            source=url_data_source,
        )

        assert job.id is not None
        assert job.status == JobStatus.QUEUED
        assert job.dataset_type == "sales"
        assert job.schema_version == "v2"
        assert job.source_type == "url"
        assert job.source_uri == "https://example.com/data.csv"
        assert isinstance(job.created_at, datetime)
        assert job.created_at.tzinfo == UTC

    def test_create_job_generates_unique_ids(self) -> None:
        job1 = job_factory()
        job2 = job_factory()

        assert job1.id != job2.id

    @pytest.mark.parametrize(
        "source_type,source_uri",
        [
            ("url", "https://example.com/data.csv"),
            ("upload", "s3://bucket/file.csv"),
        ],
    )
    def test_create_job_with_different_sources(
        self, source_type: str, source_uri: str
    ) -> None:
        job = job_factory(source_type=source_type, source_uri=source_uri)

        assert job.source_type == source_type
        assert job.source_uri == source_uri


class TestJobFromDbModel:
    """Tests for Job.from_db_model conversion"""

    def test_from_db_model(self) -> None:
        job_id = uuid4()
        created_at = datetime.now(UTC)
        db_job = DBJob(
            id=job_id,
            status="running",
            dataset_type="sales",
            schema_version="v2",
            source_type="url",
            source_uri="https://example.com/data.csv",
            created_at=created_at,
        )

        job = Job.from_db_model(db_job)

        assert job.id == job_id
        assert job.status == JobStatus.RUNNING
        assert job.dataset_type == "sales"
        assert job.schema_version == "v2"
        assert job.source_type == "url"
        assert job.source_uri == "https://example.com/data.csv"
        assert job.created_at == created_at

    @pytest.mark.parametrize("status", list(JobStatus))
    def test_from_db_model_all_statuses(self, status: JobStatus) -> None:
        db_job = DBJob(
            id=uuid4(),
            status=status.value,
            dataset_type=DEFAULTS["dataset_type"],
            schema_version=DEFAULTS["schema_version"],
            source_type=DEFAULTS["source_type"],
            source_uri=DEFAULTS["source_uri"],
            created_at=datetime.now(UTC),
        )

        job = Job.from_db_model(db_job)

        assert job.status == status


class TestJobToDbModel:
    """Tests for Job.to_db_model conversion"""

    def test_to_db_model(self, url_data_source: DataSource) -> None:
        job = Job.create_new(
            dataset_type="sales",
            schema_version="v2",
            source=url_data_source,
        )

        db_job = job.to_db_model()

        assert db_job.id == job.id
        assert db_job.status == JobStatus.QUEUED.value
        assert db_job.dataset_type == "sales"
        assert db_job.schema_version == "v2"
        assert db_job.source_type == "url"
        assert db_job.source_uri == "https://example.com/data.csv"
        assert db_job.created_at == job.created_at

    def test_to_db_model_roundtrip(self) -> None:
        original_job = job_factory(
            source_type="upload", source_uri="s3://bucket/file.csv"
        )

        db_job = original_job.to_db_model()
        restored_job = Job.from_db_model(db_job)

        assert restored_job.id == original_job.id
        assert restored_job.status == original_job.status
        assert restored_job.dataset_type == original_job.dataset_type
        assert restored_job.schema_version == original_job.schema_version
        assert restored_job.source_type == original_job.source_type
        assert restored_job.source_uri == original_job.source_uri
        assert restored_job.created_at == original_job.created_at


class TestJobTransitions:
    """Tests for Job state transitions"""

    @pytest.mark.parametrize(
        "from_status,to_status,setup_transitions",
        [
            # From QUEUED
            (JobStatus.QUEUED, JobStatus.RUNNING, []),
            (JobStatus.QUEUED, JobStatus.CANCELLED, []),
            # From RUNNING
            (JobStatus.RUNNING, JobStatus.SUCCEEDED, [JobStatus.RUNNING]),
            (JobStatus.RUNNING, JobStatus.FAILED, [JobStatus.RUNNING]),
            # From FAILED
            (
                JobStatus.FAILED,
                JobStatus.RETRY_SCHEDULED,
                [JobStatus.RUNNING, JobStatus.FAILED],
            ),
            (
                JobStatus.FAILED,
                JobStatus.CANCELLED,
                [JobStatus.RUNNING, JobStatus.FAILED],
            ),
            # From RETRY_SCHEDULED
            (
                JobStatus.RETRY_SCHEDULED,
                JobStatus.QUEUED,
                [JobStatus.RUNNING, JobStatus.FAILED, JobStatus.RETRY_SCHEDULED],
            ),
        ],
    )
    def test_valid_transitions(
        self,
        job: Job,
        from_status: JobStatus,
        to_status: JobStatus,
        setup_transitions: list[JobStatus],
    ) -> None:
        """Test all valid state transitions."""
        # Apply setup transitions to reach from_status
        for status in setup_transitions:
            job.transition_to(status)

        # Verify we're in the expected from_status
        assert job.status == from_status

        # Perform the transition
        job.transition_to(to_status)

        # Verify the transition succeeded
        assert job.status == to_status

    @pytest.mark.parametrize(
        "from_status,to_status,setup_transitions,error_msg",
        [
            # Invalid from QUEUED
            (
                JobStatus.QUEUED,
                JobStatus.SUCCEEDED,
                [],
                "Cannot transition from queued to succeeded",
            ),
            # Invalid from RUNNING
            (
                JobStatus.RUNNING,
                JobStatus.QUEUED,
                [JobStatus.RUNNING],
                "Cannot transition from running to queued",
            ),
            # Invalid from SUCCEEDED (terminal state)
            (
                JobStatus.SUCCEEDED,
                JobStatus.FAILED,
                [JobStatus.RUNNING, JobStatus.SUCCEEDED],
                "Cannot transition from succeeded to failed",
            ),
            # Invalid from CANCELLED (terminal state)
            (
                JobStatus.CANCELLED,
                JobStatus.RUNNING,
                [JobStatus.CANCELLED],
                "Cannot transition from cancelled to running",
            ),
        ],
    )
    def test_invalid_transitions(
        self,
        job: Job,
        from_status: JobStatus,
        to_status: JobStatus,
        setup_transitions: list[JobStatus],
        error_msg: str,
    ) -> None:
        """Test all invalid state transitions."""
        # Apply setup transitions to reach from_status
        for status in setup_transitions:
            job.transition_to(status)

        # Verify we're in the expected from_status
        assert job.status == from_status

        # Attempt invalid transition
        with pytest.raises(InvalidJobTransitionError, match=error_msg):
            job.transition_to(to_status)

        # Verify status unchanged
        assert job.status == from_status

    def test_full_success_flow(self, job: Job) -> None:
        """Test complete happy path: QUEUED → RUNNING → SUCCEEDED."""
        assert job.status == JobStatus.QUEUED
        job.transition_to(JobStatus.RUNNING)
        assert job.status == JobStatus.RUNNING  # type: ignore[comparison-overlap]
        job.transition_to(JobStatus.SUCCEEDED)
        assert job.status == JobStatus.SUCCEEDED

    def test_full_retry_flow(self, job: Job) -> None:
        """Test complete retry path: QUEUED → RUNNING → FAILED → RETRY_SCHEDULED → QUEUED → RUNNING → SUCCEEDED."""
        assert job.status == JobStatus.QUEUED
        job.transition_to(JobStatus.RUNNING)
        assert job.status == JobStatus.RUNNING  # type: ignore[comparison-overlap]
        job.transition_to(JobStatus.FAILED)
        assert job.status == JobStatus.FAILED
        job.transition_to(JobStatus.RETRY_SCHEDULED)
        assert job.status == JobStatus.RETRY_SCHEDULED
        job.transition_to(JobStatus.QUEUED)
        assert job.status == JobStatus.QUEUED
        job.transition_to(JobStatus.RUNNING)
        assert job.status == JobStatus.RUNNING
        job.transition_to(JobStatus.SUCCEEDED)
        assert job.status == JobStatus.SUCCEEDED
