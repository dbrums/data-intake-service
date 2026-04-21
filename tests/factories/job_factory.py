from typing import Any

from app.domains.job import DataSource, Job
from app.schemas.job import JobCreate

DEFAULTS: dict[str, Any] = {
    "dataset_type": "test",
    "schema_version": "v1",
    "source_type": "url",
    "source_uri": "https://example.com/data.csv",
}


def job_factory(**overrides: Any) -> Job:
    """Factory for creating Job instances with sensible defaults."""
    params = DEFAULTS | overrides
    data_source = DataSource(params.pop("source_type"), params.pop("source_uri"))
    params["source"] = data_source
    return Job.create_new(**params)


def job_create_factory(**overrides: Any) -> JobCreate:
    """Factory for creating JobCreate instances with sensible defaults."""
    defaults = {k: v for k, v in DEFAULTS.items() if k != "status"}
    return JobCreate(**(defaults | overrides))
