from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from app.db.models.job import Job as DBJob


class InvalidJobTransitionError(Exception):
    pass


@dataclass
class DataSource:
    """Value object - no identity"""

    type: str
    uri: str

    def __post_init__(self) -> None:
        if self.type not in ("url", "upload"):
            raise ValueError(f"Invalid source type: {self.type}")


class JobStatus(Enum):
    """Explicit state enumeration"""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY_SCHEDULED = "retry_scheduled"


@dataclass
class Job:
    id: UUID
    status: JobStatus
    dataset_type: str
    schema_version: str
    source_type: str
    source_uri: str
    created_at: datetime

    @classmethod
    def create_new(
        cls, dataset_type: str, schema_version: str, source: DataSource
    ) -> Job:
        return cls(
            id=uuid4(),
            status=JobStatus.QUEUED,
            dataset_type=dataset_type,
            schema_version=schema_version,
            source_type=source.type,
            source_uri=source.uri,
            created_at=datetime.now(UTC),
        )

    @classmethod
    def from_db_model(cls, db_job: DBJob) -> Job:
        return cls(
            id=db_job.id,
            dataset_type=db_job.dataset_type,
            schema_version=db_job.schema_version,
            source_type=db_job.source_type,
            source_uri=db_job.source_uri,
            status=JobStatus(db_job.status),
            created_at=db_job.created_at,
        )

    def to_db_model(self) -> DBJob:
        return DBJob(
            id=self.id,
            status=self.status.value,
            dataset_type=self.dataset_type,
            schema_version=self.schema_version,
            source_type=self.source_type,
            source_uri=self.source_uri,
            created_at=self.created_at,
        )

    def transition_to(self, new_status: JobStatus) -> None:
        """Business rule: validate state transitions"""
        if not self._is_valid_transition(new_status):
            raise InvalidJobTransitionError(
                f"Cannot transition from {self.status} to {new_status}"
            )

        self.status = new_status

    def _is_valid_transition(self, new_status: JobStatus) -> bool:
        """FSM transition rules"""
        VALID_TRANSITIONS = {
            JobStatus.QUEUED: {JobStatus.RUNNING, JobStatus.CANCELLED},
            JobStatus.RUNNING: {JobStatus.SUCCEEDED, JobStatus.FAILED},
            JobStatus.FAILED: {JobStatus.RETRY_SCHEDULED, JobStatus.CANCELLED},
            JobStatus.RETRY_SCHEDULED: {JobStatus.QUEUED},
            JobStatus.SUCCEEDED: set(),  # Terminal state
            JobStatus.CANCELLED: set(),  # Terminal state
        }
        return new_status in VALID_TRANSITIONS[self.status]
