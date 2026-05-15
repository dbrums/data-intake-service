from time import sleep
from uuid import UUID

from app.core.logging.context import set_job_id
from app.db.session import SessionLocal
from app.repositories.job_repository import SqlAlchemyJobRepository
from app.schemas.job import JobFail
from app.services.job_service import JobService


def execute_validation_job(job_id: UUID) -> None:
    """Worker task to execute validation job (Phase 4: mock validation)."""

    # Manual dependency instantiation (standard RQ pattern)
    db = SessionLocal()
    service = None

    try:
        repo = SqlAlchemyJobRepository(db)
        service = JobService(repo)

        # Set logging context
        set_job_id(job_id)

        # Start job
        service.start_job(job_id)

        # Mock validation (replace in Phase 5)
        sleep(3)  # Simulate work

        # Complete job
        service.complete_job(job_id)

    except Exception as e:
        # Log and mark as failed (only if service was successfully created)
        if service is not None:
            fail_payload = JobFail(
                error_code="WORKER_ERROR",
                error_message=str(e)[:500],  # Truncate to max length
            )
            service.fail_job(fail_payload, job_id)
        raise  # Re-raise for RQ retry handling (Phase 6)
    finally:
        db.close()
