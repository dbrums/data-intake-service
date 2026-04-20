from uuid import uuid4

from sqlalchemy.orm import Session

from app.domains.job import Job
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
