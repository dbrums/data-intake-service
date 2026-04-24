from uuid import uuid4

from app.domains.job import Job, JobStatus
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


def test_fake_job_repo_list_all_returns_empty_list(fake_job_repo: FakeJobRepository):
    jobs = fake_job_repo.list_all()

    assert jobs == []


def test_fake_job_repo_list_all_returns_single_job(
    fake_job_repo: FakeJobRepository, job: Job
):
    created_job = fake_job_repo.create(job)

    jobs = fake_job_repo.list_all()

    assert len(jobs) == 1
    assert jobs[0].id == created_job.id


def test_fake_job_repo_list_all_returns_multiple_jobs(
    fake_job_repo: FakeJobRepository, job: Job
):
    from app.domains.job import DataSource

    job1 = fake_job_repo.create(job)
    job2 = Job.create_new(
        dataset_type="another_type",
        schema_version="v2",
        source=DataSource(type=job.source_type, uri=job.source_uri),
    )
    job2 = fake_job_repo.create(job2)
    job3 = Job.create_new(
        dataset_type="third_type",
        schema_version="v3",
        source=DataSource(type=job.source_type, uri=job.source_uri),
    )
    job3 = fake_job_repo.create(job3)

    jobs = fake_job_repo.list_all()

    assert len(jobs) == 3
    job_ids = [j.id for j in jobs]
    assert job1.id in job_ids
    assert job2.id in job_ids
    assert job3.id in job_ids


def test_fake_job_repository_update(fake_job_repo: FakeJobRepository, job: Job):
    created_job = fake_job_repo.create(job)
    created_job.status = JobStatus.RUNNING
    updated_job = fake_job_repo.update(job)

    assert created_job.id == updated_job.id
    assert created_job.status == JobStatus.RUNNING
