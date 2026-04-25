import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_job_service
from app.domains.job import InvalidJobTransitionError
from app.schemas.job import JobCreate, JobFail, JobRead
from app.services.job_service import JobNotFoundError, JobService

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
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except Exception:
        logger.error("get job request failed", exc_info=True)
        raise


@router.get("", response_model=list[JobRead], status_code=status.HTTP_200_OK)
def get_jobs(service: JobService = Depends(get_job_service)) -> list[JobRead]:
    logger.info("received get jobs request")
    try:
        jobs = service.get_jobs()
        logger.info("get jobs request completed successfully")
        return [JobRead.model_validate(job) for job in jobs]
    except Exception:
        logger.error("get jobs request failed", exc_info=True)
        raise


@router.patch("/{job_id}/start", response_model=JobRead, status_code=status.HTTP_200_OK)
def patch_job_start(
    job_id: UUID, service: JobService = Depends(get_job_service)
) -> JobRead:
    logger.info("received job start request")
    try:
        job = service.start_job(job_id)
        logger.info("start job request completed successfully")
        return JobRead.model_validate(job)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except InvalidJobTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception:
        logger.error("start jobs request failed", exc_info=True)
        raise


@router.patch(
    "/{job_id}/complete", response_model=JobRead, status_code=status.HTTP_200_OK
)
def patch_job_complete(
    job_id: UUID, service: JobService = Depends(get_job_service)
) -> JobRead:
    logger.info("received job complete request")
    try:
        job = service.complete_job(job_id)
        logger.info("complete job request completed successfully")
        return JobRead.model_validate(job)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except InvalidJobTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception:
        logger.error("complete jobs request failed", exc_info=True)
        raise


@router.patch("/{job_id}/fail", response_model=JobRead, status_code=status.HTTP_200_OK)
def patch_job_fail(
    job_id: UUID, payload: JobFail, service: JobService = Depends(get_job_service)
) -> JobRead:
    logger.info("received job fail request")
    try:
        job = service.fail_job(payload, job_id)
        logger.info("fail job request completed successfully")
        return JobRead.model_validate(job)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except InvalidJobTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception:
        logger.error("fail jobs request failed", exc_info=True)
        raise


@router.post("/{job_id}/retry", response_model=JobRead, status_code=status.HTTP_200_OK)
def post_job_retry(
    job_id: UUID, service: JobService = Depends(get_job_service)
) -> JobRead:
    logger.info("received job retry request")
    try:
        job = service.retry_job(job_id)
        logger.info("retry job request completed successfully")
        return JobRead.model_validate(job)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except InvalidJobTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception:
        logger.error("retry job request failed", exc_info=True)
        raise


@router.delete("/{job_id}", response_model=JobRead, status_code=status.HTTP_200_OK)
def delete_job(job_id: UUID, service: JobService = Depends(get_job_service)) -> JobRead:
    logger.info("received job cancel request")
    try:
        job = service.cancel_job(job_id)
        logger.info("cancel job request completed successfully")
        return JobRead.model_validate(job)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except InvalidJobTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception:
        logger.error("cancel job request failed", exc_info=True)
        raise
