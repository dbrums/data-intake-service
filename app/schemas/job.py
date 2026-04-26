from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    dataset_type: str
    schema_version: str = Field(default="v1")
    source_type: str
    source_uri: str
    idempotency_key: str | None = Field(default=None)


class JobRead(BaseModel):
    model_config = {"from_attributes": True}

    job_id: UUID = Field(alias="id")
    status: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    error_code: str | None
    error_message: str | None
    retry_count: int


class JobGetByID(BaseModel):
    job_id: UUID


class JobFail(BaseModel):
    error_code: str = Field(max_length=50, pattern=r"^[A-Z_0-9]+$")
    error_message: str = Field(max_length=500, min_length=1)
