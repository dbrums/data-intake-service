from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobCreate, JobRead
from app.services.job_service import JobService

router = APIRouter()


@router.post("", response_model=JobRead)
def create_job(payload: JobCreate, db: Session = Depends(get_db)) -> JobRead:
    repo = JobRepository(db)
    service = JobService(repo)
    job = service.create_job(payload)
    return JobRead.model_validate(job)
