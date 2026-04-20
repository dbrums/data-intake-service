from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import get_job_service
from app.schemas.job import JobCreate, JobRead
from app.services.job_service import JobService

router = APIRouter()


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate, service: JobService = Depends(get_job_service)
) -> JobRead:
    job = service.create_job(payload)
    return JobRead.model_validate(job)


@router.get("/{job_id}", response_model=JobRead, status_code=status.HTTP_200_OK)
def get_job_by_id(
    job_id: UUID, service: JobService = Depends(get_job_service)
) -> JobRead:
    job = service.get_job_by_id(job_id)
    return JobRead.model_validate(job)
