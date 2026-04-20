from uuid import uuid4

from app.domains.job import Job
from tests.fakes.fake_job_repository import FakeJobRepository


def test_fake_job_repo_create(fake_job_repo: FakeJobRepository, job: Job):
    created_job = fake_job_repo.create(job)

    assert created_job.id is not None
    attr_list = [
        "dataset_type",
        "schema_version",
        "source_type",
        "source_uri",
        "status",
    ]
    for field in attr_list:
        assert getattr(created_job, field) == getattr(job, field)


def test_fake_job_repo_get_by_id(fake_job_repo: FakeJobRepository, job: Job):
    created_job = fake_job_repo.create(job)
    assert fake_job_repo.get_by_id(created_job.id) == created_job


def test_fake_job_repo_get_by_id_not_found(fake_job_repo: FakeJobRepository):
    non_existent_id = uuid4()
    assert fake_job_repo.get_by_id(non_existent_id) is None
