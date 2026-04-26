from collections.abc import Callable
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.domains.job import JobStatus
from app.schemas.job import JobCreate, JobFail


@pytest.fixture
def job_in_status(
    client: TestClient, job_create: Callable[..., JobCreate], job_fail: JobFail
) -> Callable[[JobStatus], UUID]:
    def _create_job(status: JobStatus) -> UUID:
        create_response = client.post("/api/v1/jobs", json=job_create().model_dump())
        job_id = create_response.json()["id"]

        if status == JobStatus.RUNNING:
            client.patch(f"/api/v1/jobs/{job_id}/start")
        elif status == JobStatus.FAILED:
            client.patch(f"/api/v1/jobs/{job_id}/start")
            client.patch(f"/api/v1/jobs/{job_id}/fail", json=job_fail.model_dump())

        return job_id

    return _create_job


def test_post_jobs_returns_201_and_body(
    client: TestClient, job_create: Callable[..., JobCreate]
):
    response = client.post("/api/v1/jobs", json=job_create().model_dump())

    assert response.status_code == 201

    body = response.json()
    assert body["id"] is not None
    assert body["status"] == JobStatus.QUEUED.value


def test_post_jobs_with_idempotency_key_returns_same_job(
    client: TestClient, job_create: Callable[..., JobCreate]
):
    create_response = client.post(
        "/api/v1/jobs", json=job_create(idempotency_key="my-key").model_dump()
    )

    idempotent_create_response = client.post(
        "/api/v1/jobs", json=job_create(idempotency_key="my-key").model_dump()
    )

    assert create_response.json()["id"] == idempotent_create_response.json()["id"]
    assert create_response.status_code == 201
    assert idempotent_create_response.status_code == 201


def test_post_jobs_with_idempotency_key_different_params_returns_409(
    client: TestClient, job_create: Callable[..., JobCreate]
):
    payload1 = job_create(idempotency_key="test-key-456", dataset_type="type1")
    payload2 = job_create(idempotency_key="test-key-456", dataset_type="type2")

    response1 = client.post("/api/v1/jobs", json=payload1.model_dump())
    response2 = client.post("/api/v1/jobs", json=payload2.model_dump())

    assert response1.status_code == 201
    assert response2.status_code == 409
    assert "different parameters" in response2.json()["detail"]


def test_post_jobs_with_idempotency_key_terminal_state_returns_409(
    client: TestClient, job_create: Callable[..., JobCreate]
):
    payload = job_create(idempotency_key="test-key-789")
    response1 = client.post("/api/v1/jobs", json=payload.model_dump())
    job_id = response1.json()["id"]

    # Complete the job (terminal state)
    client.patch(f"/api/v1/jobs/{job_id}/start")
    client.patch(f"/api/v1/jobs/{job_id}/complete")

    # Try to create again with same idempotency key
    response2 = client.post("/api/v1/jobs", json=payload.model_dump())

    assert response1.status_code == 201
    assert response2.status_code == 409
    assert "cannot be retried" in response2.json()["detail"].lower()


def test_post_jobs_invalid_payload_returns_422(client: TestClient):
    response = client.post("/api/v1/jobs", json={"name": 123})

    assert response.status_code == 422


def test_get_job_returns_200(client: TestClient, job_create: Callable[..., JobCreate]):
    create_response = client.post("/api/v1/jobs", json=job_create().model_dump())
    job_id = create_response.json()["id"]

    response = client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["id"] == job_id
    assert response.json()["status"] == JobStatus.QUEUED.value


def test_get_missing_job_returns_404(client: TestClient):
    response = client.get(f"/api/v1/jobs/{uuid4()}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_jobs_returns_empty_list_when_no_jobs(client: TestClient):
    response = client.get("/api/v1/jobs")

    assert response.status_code == 200
    assert response.json() == []


def test_get_jobs_returns_200(client: TestClient, job_create: Callable[..., JobCreate]):
    create_response = client.post("/api/v1/jobs", json=job_create().model_dump())
    job_id = create_response.json()["id"]

    response = client.get("/api/v1/jobs")

    assert response.status_code == 200
    jobs: list[dict[str, object]] = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) == 1
    assert jobs[0]["id"] == job_id
    assert jobs[0]["status"] == JobStatus.QUEUED.value


def test_get_jobs_returns_all_jobs(
    client: TestClient, job_create: Callable[..., JobCreate]
):
    job_ids: list[str] = []
    for _ in range(3):
        response = client.post("/api/v1/jobs", json=job_create().model_dump())
        job_ids.append(response.json()["id"])

    response = client.get("/api/v1/jobs")

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 3
    returned_ids = [job["id"] for job in jobs]
    assert set(returned_ids) == set(job_ids)
    for job in jobs:
        assert job["status"] == JobStatus.QUEUED.value


def test_patch_job_start_returns_200(
    client: TestClient, job_create: Callable[..., JobCreate]
):
    create_response = client.post("/api/v1/jobs", json=job_create().model_dump())
    job_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/jobs/{job_id}/start")
    assert response.status_code == 200
    assert response.json()["status"] == JobStatus.RUNNING.value
    assert response.json()["started_at"] is not None
    assert response.json()["created_at"] <= response.json()["started_at"]


def test_patch_job_start_nonexistent_job_returns_404(client: TestClient):
    response = client.patch(f"/api/v1/jobs/{uuid4()}/start")
    assert response.status_code == 404


def test_patch_job_start_on_running_job_returns_409(
    client: TestClient, job_create: Callable[..., JobCreate]
):
    create_response = client.post("/api/v1/jobs", json=job_create().model_dump())
    job_id = create_response.json()["id"]

    client.patch(f"/api/v1/jobs/{job_id}/start")

    # Try to start again (invalid transition: RUNNING → RUNNING)
    response = client.patch(f"/api/v1/jobs/{job_id}/start")
    assert response.status_code == 409


def test_patch_job_complete_returns_200(
    client: TestClient, job_create: Callable[..., JobCreate]
):
    create_response = client.post("/api/v1/jobs", json=job_create().model_dump())
    job_id = create_response.json()["id"]
    start_response = client.patch(f"/api/v1/jobs/{job_id}/start")
    job_id = start_response.json()["id"]

    response = client.patch(f"/api/v1/jobs/{job_id}/complete")
    assert response.status_code == 200
    assert response.json()["status"] == JobStatus.SUCCEEDED.value
    assert response.json()["finished_at"] is not None
    assert response.json()["created_at"] <= response.json()["started_at"]
    assert response.json()["started_at"] <= response.json()["finished_at"]


def test_patch_job_complete_nonexistent_job_returns_404(client: TestClient):
    response = client.patch(f"/api/v1/jobs/{uuid4()}/complete")
    assert response.status_code == 404


def test_patch_job_fail_returns_200(
    client: TestClient, job_create: Callable[..., JobCreate], job_fail: JobFail
):
    create_response = client.post("/api/v1/jobs", json=job_create().model_dump())
    job_id = create_response.json()["id"]
    start_response = client.patch(f"/api/v1/jobs/{job_id}/start")
    job_id = start_response.json()["id"]

    response = client.patch(f"/api/v1/jobs/{job_id}/fail", json=job_fail.model_dump())
    assert response.status_code == 200
    assert response.json()["status"] == JobStatus.FAILED.value
    assert response.json()["error_code"] == job_fail.error_code
    assert response.json()["error_message"] == job_fail.error_message
    assert response.json()["finished_at"] is not None


def test_patch_job_fail_nonexistent_job_returns_404(
    client: TestClient, job_fail: JobFail
):
    response = client.patch(f"/api/v1/jobs/{uuid4()}/fail", json=job_fail.model_dump())
    assert response.status_code == 404


def test_post_job_retry_returns_200(
    client: TestClient, job_create: Callable[..., JobCreate], job_fail: JobFail
):
    create_response = client.post("/api/v1/jobs", json=job_create().model_dump())
    job_id = create_response.json()["id"]
    start_response = client.patch(f"/api/v1/jobs/{job_id}/start")
    job_id = start_response.json()["id"]

    fail_response = client.patch(
        f"/api/v1/jobs/{job_id}/fail", json=job_fail.model_dump()
    )
    job_id = fail_response.json()["id"]

    retry_response = client.post(f"/api/v1/jobs/{job_id}/retry")
    assert retry_response.status_code == 200
    assert retry_response.json()["status"] == JobStatus.QUEUED.value
    assert retry_response.json()["started_at"] is None
    assert retry_response.json()["finished_at"] is None


def test_post_job_retry_nonexistent_job_returns_404(client: TestClient):
    response = client.post(f"/api/v1/jobs/{uuid4()}/retry")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "status",
    [JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.FAILED, JobStatus.RETRY_SCHEDULED],
)
def test_delete_job_returns_200(
    client: TestClient, job_in_status: Callable[[JobStatus], UUID], status: JobStatus
):
    job_id = job_in_status(status)
    delete_response = client.delete(f"/api/v1/jobs/{job_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == JobStatus.CANCELLED.value
    assert delete_response.json()["finished_at"] is not None


def test_delete_job_nonexistent_job_returns_404(client: TestClient):
    response = client.delete(f"/api/v1/jobs/{uuid4()}")
    assert response.status_code == 404


def test_delete_job_from_succeeded_returns_409(
    client: TestClient, job_create: Callable[..., JobCreate]
):
    # Create and complete job
    response = client.post("/api/v1/jobs", json=job_create().model_dump())
    job_id = response.json()["id"]
    client.patch(f"/api/v1/jobs/{job_id}/start")
    client.patch(f"/api/v1/jobs/{job_id}/complete")

    # Attempt to cancel completed job
    delete_response = client.delete(f"/api/v1/jobs/{job_id}")

    assert delete_response.status_code == 409
    assert (
        "cannot transition from succeeded to cancelled"
        in delete_response.json()["detail"].lower()
    )
