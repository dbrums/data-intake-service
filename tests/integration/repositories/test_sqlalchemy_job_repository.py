from uuid import uuid4

from sqlalchemy.orm import Session

from app.domains.job import DataSource, Job
from app.repositories.job_repository import SqlAlchemyJobRepository


def test_job_repository_create(db_session: Session, job: Job):
    repo = SqlAlchemyJobRepository(db_session)
    created_job = repo.create(job)
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


def test_job_repo_get_by_id(db_session: Session, job: Job):
    repo = SqlAlchemyJobRepository(db_session)
    created_job = repo.create(job)
    assert repo.get_by_id(created_job.id) == created_job


def test_job_repo_get_by_id_not_found(db_session: Session):
    repo = SqlAlchemyJobRepository(db_session)
    non_existent_id = uuid4()
    assert repo.get_by_id(non_existent_id) is None


def test_job_repo_list_all_empty(db_session: Session):
    repo = SqlAlchemyJobRepository(db_session)

    jobs = repo.list_all()

    assert jobs == []


def test_job_repo_list_all_single_job(db_session: Session):
    repo = SqlAlchemyJobRepository(db_session)
    source = DataSource(type="url", uri="https://example.com/data.csv")
    job = Job.create_new(
        dataset_type="test",
        schema_version="v1",
        source=source,
    )
    created_job = repo.create(job)

    jobs = repo.list_all()

    assert len(jobs) == 1
    assert jobs[0].id == created_job.id
    assert jobs[0].dataset_type == "test"
    assert jobs[0].schema_version == "v1"


def test_job_repo_list_all_multiple_jobs(db_session: Session):
    repo = SqlAlchemyJobRepository(db_session)
    source = DataSource(type="url", uri="https://example.com/data.csv")

    job1 = repo.create(Job.create_new("type1", "v1", source))
    job2 = repo.create(Job.create_new("type2", "v2", source))
    job3 = repo.create(Job.create_new("type3", "v3", source))

    jobs = repo.list_all()

    assert len(jobs) == 3
    job_ids = [j.id for j in jobs]
    assert job1.id in job_ids
    assert job2.id in job_ids
    assert job3.id in job_ids
