from app.domains.job import JobStatus
from app.schemas.job import JobCreate
from app.services.job_service import JobService
from tests.factories.job_factory import DEFAULTS
from tests.fakes.fake_job_repository import FakeJobRepository


def test_job_service_create_job(
    fake_job_repo: FakeJobRepository, job_create: JobCreate
):
    service = JobService(fake_job_repo)
    job = service.create_job(job_create)

    assert job.id is not None
    assert job.status == JobStatus.QUEUED
    attr_list = [
        "dataset_type",
        "schema_version",
        "source_type",
        "source_uri",
    ]
    for field in attr_list:
        assert getattr(job, field) == DEFAULTS.get(field)
