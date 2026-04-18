from collections.abc import Generator
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.db.models.job import Job
from app.schemas.job import JobCreate
from app.main import app
from tests.factories.job_factory import job_factory, job_create_factory
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
def db_engine() -> Generator[Engine, None, None]:
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
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
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
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
