from fastapi.testclient import TestClient

from app.schemas.job import JobCreate


def test_post_jobs_returns_201_and_body(client: TestClient, job_create: JobCreate):
    response = client.post("/api/v1/jobs", json=job_create.model_dump())

    assert response.status_code == 201

    body = response.json()
    assert body["id"] is not None
    assert body["status"] == "queued"


# def test_get_job_returns_200(client: TestClient, job_create: JobCreate):
#     create_response = client.post("/api/v1/jobs", json=job_create.model_dump())
#     job_id = create_response.json()["id"]

#     response = client.get(f"/api/v1/jobs/{job_id}")

#     assert response.status_code == 200
#     assert response.json()["id"] == job_id
#     assert response.json()["status"] == "queued"


# def test_get_missing_job_returns_404(client: TestClient):
#     response = client.get("/api/v1/jobs/999")

#     assert response.status_code == 404
#     assert "not found" in response.json()["detail"]


def test_post_jobs_invalid_payload_returns_422(client: TestClient):
    response = client.post("/api/v1/jobs", json={"name": 123})

    assert response.status_code == 422
