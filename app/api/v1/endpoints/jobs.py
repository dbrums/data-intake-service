import logging
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import get_job_service
from app.schemas.job import JobCreate, JobRead
from app.services.job_service import JobService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate, service: JobService = Depends(get_job_service)
) -> JobRead:
    logger.info("received job creation request")
    try:
        job = service.create_job(payload)
        logger.info("job creation request completed successfully")
        return JobRead.model_validate(job)
    except Exception:
        logger.error("job creation request failed", exc_info=True)
        raise


@router.get("/{job_id}", response_model=JobRead, status_code=status.HTTP_200_OK)
def get_job_by_id(
    job_id: UUID, service: JobService = Depends(get_job_service)
) -> JobRead:
    logger.info("received get job request")
    try:
        job = service.get_job_by_id(job_id)
        logger.info("get job request completed successfully")
        return JobRead.model_validate(job)
    except Exception:
        logger.error("get job request failed", exc_info=True)
        raise
