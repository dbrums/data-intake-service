import logging
from contextvars import ContextVar
from logging import LogRecord
from uuid import UUID

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
job_id_var: ContextVar[UUID | None] = ContextVar("job_id", default=None)


class ContextFilter(logging.Filter):
    def __init__(self, name: str = ""):
        super().__init__(name)
        from app.core.config import settings

        self.environment = settings.ENV
        self.service_name = settings.APP_NAME

    def filter(self, record: LogRecord) -> bool:
        # Static context
        record.environment = self.environment
        record.service_name = self.service_name

        # Request-scoped context
        record.request_id = request_id_var.get()
        job_id = job_id_var.get()
        record.job_id = str(job_id) if job_id else None

        return True


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current context."""
    request_id_var.set(request_id)


def set_job_id(job_id: UUID) -> None:
    """Set the job ID for the current context."""
    job_id_var.set(job_id)


def clear_context() -> None:
    """Clear all context variables."""
    request_id_var.set(None)
    job_id_var.set(None)
