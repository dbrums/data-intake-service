from fastapi import APIRouter

from app.api.v1.endpoints.jobs import router as jobs_router

v1_router = APIRouter()
v1_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
