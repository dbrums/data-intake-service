import logging
from uuid import uuid4

import pytest

from app.core.logging.context import (
    ContextFilter,
    clear_context,
    set_job_id,
    set_request_id,
)


@pytest.fixture(autouse=True)
def cleanup_context():
    """Clear context after each test."""
    yield
    clear_context()


def test_context_filter_adds_request_id():
    """Verify ContextFilter adds request_id to log records."""
    context_filter = ContextFilter()
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="test",
        args=(),
        exc_info=None,
    )

    request_id = "test-request-123"
    set_request_id(request_id)
    context_filter.filter(record)

    assert record.request_id == request_id  # type: ignore[attr-defined]


def test_context_filter_adds_job_id():
    """Verify ContextFilter adds job_id to log records."""
    context_filter = ContextFilter()
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="test",
        args=(),
        exc_info=None,
    )

    job_id = uuid4()
    set_job_id(job_id)
    context_filter.filter(record)

    assert record.job_id == str(job_id)  # type: ignore[attr-defined]


def test_context_filter_adds_static_fields():
    """Verify ContextFilter adds environment and service_name to log records."""
    context_filter = ContextFilter()
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="test",
        args=(),
        exc_info=None,
    )

    context_filter.filter(record)

    assert hasattr(record, "environment")
    assert hasattr(record, "service_name")
    assert record.service_name == "data-intake-service"  # type: ignore[attr-defined]


def test_clear_context_removes_ids():
    """Verify clear_context removes request and job IDs."""
    context_filter = ContextFilter()
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="test",
        args=(),
        exc_info=None,
    )

    request_id = "test-request-456"
    job_id = uuid4()
    set_request_id(request_id)
    set_job_id(job_id)
    clear_context()
    context_filter.filter(record)

    assert record.request_id is None  # type: ignore[attr-defined]
    assert record.job_id is None  # type: ignore[attr-defined]


def test_all_context_fields_present():
    """Verify all context fields are present in log records."""
    context_filter = ContextFilter()
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="test",
        args=(),
        exc_info=None,
    )

    request_id = "test-request-789"
    job_id = uuid4()
    set_request_id(request_id)
    set_job_id(job_id)
    context_filter.filter(record)

    assert record.request_id == request_id  # type: ignore[attr-defined]
    assert record.job_id == str(job_id)  # type: ignore[attr-defined]
    assert record.environment is not None  # type: ignore[attr-defined]
    assert record.service_name == "data-intake-service"  # type: ignore[attr-defined]
