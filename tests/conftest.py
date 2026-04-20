from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_job_repository
from app.db.base import Base
from app.domains.job import Job
from app.main import app
from app.schemas.job import JobCreate
from tests.factories.job_factory import job_create_factory, job_factory
from tests.fakes.fake_job_repository import FakeJobRepository

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def fake_job_repo() -> FakeJobRepository:
    return FakeJobRepository()


@pytest.fixture
def job() -> Job:
    return job_factory()


@pytest.fixture
def job_create() -> JobCreate:
    return job_create_factory()


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine]:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session]:
    TestingSessionLocal = sessionmaker(
        bind=db_engine,
        autoflush=False,
        autocommit=False,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(fake_job_repo: FakeJobRepository) -> Generator[TestClient]:
    def override_get_job_repository() -> FakeJobRepository:
        return fake_job_repo

    app.dependency_overrides[get_job_repository] = override_get_job_repository

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
