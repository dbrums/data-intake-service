from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.domains.job import JobStatus
from app.schemas.job import JobCreate
from app.services.job_service import JobNotFoundError


def test_post_jobs_returns_201_and_body(client: TestClient, job_create: JobCreate):
    response = client.post("/api/v1/jobs", json=job_create.model_dump())

    assert response.status_code == 201

    body = response.json()
    assert body["id"] is not None
    assert body["status"] == JobStatus.QUEUED.value


def test_get_job_returns_200(client: TestClient, job_create: JobCreate):
    create_response = client.post("/api/v1/jobs", json=job_create.model_dump())
    job_id = create_response.json()["id"]

    response = client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["id"] == job_id
    assert response.json()["status"] == JobStatus.QUEUED.value


def test_get_missing_job_returns_404(client: TestClient):
    with pytest.raises(JobNotFoundError):
        response = client.get(f"/api/v1/jobs/{uuid4()}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_post_jobs_invalid_payload_returns_422(client: TestClient):
    response = client.post("/api/v1/jobs", json={"name": 123})

    assert response.status_code == 422
