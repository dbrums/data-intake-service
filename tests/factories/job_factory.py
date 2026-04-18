from typing import Any

from app.db.models.job import Job
from app.schemas.job import JobCreate


DEFAULTS = {
    "dataset_type": "test",
    "schema_version": "v1",
    "source_type": "url",
    "source_uri": "https://example.com/data.csv",
    "status": "queued",
}


def job_factory(**overrides: Any):
    """Factory for creating Job instances with sensible defaults."""
    return Job(**(DEFAULTS | overrides))


def job_create_factory(**overrides: Any):
    """Factory for creating JobCreate instances with sensible defaults."""
    defaults = {k: v for k, v in DEFAULTS.items() if k != "status"}
    return JobCreate(**(defaults | overrides))
