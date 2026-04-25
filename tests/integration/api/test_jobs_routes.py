from uuid import uuid4

from fastapi.testclient import TestClient

from app.domains.job import JobStatus
from app.schemas.job import JobCreate, JobFail


def test_post_jobs_returns_201_and_body(client: TestClient, job_create: JobCreate):
    response = client.post("/api/v1/jobs", json=job_create.model_dump())

    assert response.status_code == 201

    body = response.json()
    assert body["id"] is not None
    assert body["status"] == JobStatus.QUEUED.value


def test_post_jobs_invalid_payload_returns_422(client: TestClient):
    response = client.post("/api/v1/jobs", json={"name": 123})

    assert response.status_code == 422


def test_get_job_returns_200(client: TestClient, job_create: JobCreate):
    create_response = client.post("/api/v1/jobs", json=job_create.model_dump())
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


def test_get_jobs_returns_200(client: TestClient, job_create: JobCreate):
    create_response = client.post("/api/v1/jobs", json=job_create.model_dump())
    job_id = create_response.json()["id"]

    response = client.get("/api/v1/jobs")

    assert response.status_code == 200
    jobs: list[dict[str, object]] = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) == 1
    assert jobs[0]["id"] == job_id
    assert jobs[0]["status"] == JobStatus.QUEUED.value


def test_get_jobs_returns_all_jobs(client: TestClient, job_create: JobCreate):
    job_ids: list[str] = []
    for _ in range(3):
        response = client.post("/api/v1/jobs", json=job_create.model_dump())
        job_ids.append(response.json()["id"])

    response = client.get("/api/v1/jobs")

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 3
    returned_ids = [job["id"] for job in jobs]
    assert set(returned_ids) == set(job_ids)
    for job in jobs:
        assert job["status"] == JobStatus.QUEUED.value


def test_patch_job_start_returns_200(client: TestClient, job_create: JobCreate):
    create_response = client.post("/api/v1/jobs", json=job_create.model_dump())
    job_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/jobs/{job_id}/start")
    assert response.status_code == 200
    assert response.json()["status"] == JobStatus.RUNNING.value
    assert response.json()["started_at"] is not None


def test_patch_job_start_nonexistent_job_returns_404(client: TestClient):
    response = client.patch(f"/api/v1/jobs/{uuid4()}/start")
    assert response.status_code == 404


def test_patch_job_start_on_running_job_returns_409(
    client: TestClient, job_create: JobCreate
):
    create_response = client.post("/api/v1/jobs", json=job_create.model_dump())
    job_id = create_response.json()["id"]

    client.patch(f"/api/v1/jobs/{job_id}/start")

    # Try to start again (invalid transition: RUNNING → RUNNING)
    response = client.patch(f"/api/v1/jobs/{job_id}/start")
    assert response.status_code == 409


def test_patch_job_complete_returns_200(client: TestClient, job_create: JobCreate):
    create_response = client.post("/api/v1/jobs", json=job_create.model_dump())
    job_id = create_response.json()["id"]
    start_response = client.patch(f"/api/v1/jobs/{job_id}/start")
    job_id = start_response.json()["id"]

    response = client.patch(f"/api/v1/jobs/{job_id}/complete")
    assert response.status_code == 200
    assert response.json()["status"] == JobStatus.SUCCEEDED.value
    assert response.json()["finished_at"] is not None
    assert response.json()["started_at"] <= response.json()["finished_at"]


def test_patch_job_complete_nonexistent_job_returns_404(client: TestClient):
    response = client.patch(f"/api/v1/jobs/{uuid4()}/complete")
    assert response.status_code == 404


def test_patch_job_fail_returns_200(
    client: TestClient, job_create: JobCreate, job_fail: JobFail
):
    create_response = client.post("/api/v1/jobs", json=job_create.model_dump())
    job_id = create_response.json()["id"]
    start_response = client.patch(f"/api/v1/jobs/{job_id}/start")
    job_id = start_response.json()["id"]

    response = client.patch(f"/api/v1/jobs/{job_id}/fail", json=job_fail.model_dump())
    assert response.status_code == 200
    assert response.json()["status"] == JobStatus.FAILED.value


def test_patch_job_fail_nonexistent_job_returns_404(
    client: TestClient, job_fail: JobFail
):
    response = client.patch(f"/api/v1/jobs/{uuid4()}/fail", json=job_fail.model_dump())
    assert response.status_code == 404
