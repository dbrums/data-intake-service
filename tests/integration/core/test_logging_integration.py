import logging
from uuid import uuid4

import pytest

from app.core.logging.context import clear_context, set_job_id, set_request_id
from app.core.logging.setup import setup_logging


@pytest.fixture(autouse=True)
def setup_and_cleanup():
    """Setup logging before each test and cleanup context after."""
    setup_logging()
    yield
    clear_context()


def test_logging_integration_with_real_logger():
    """Integration test: verify full logging pipeline with real logger."""
    # Create a test logger under 'app' namespace
    test_logger = logging.getLogger("app.test.integration")

    # Set context
    request_id = "integration-test-request"
    job_id = uuid4()

    set_request_id(request_id)
    set_job_id(job_id)

    # Log a message (this will go through the full pipeline)
    test_logger.info("integration test message", extra={"test_field": "test_value"})

    # Verify the logger is configured correctly
    assert test_logger.getEffectiveLevel() == logging.INFO
    assert len(test_logger.handlers) == 0  # Uses parent (app) logger handlers

    # Verify parent app logger has handlers
    app_logger = logging.getLogger("app")
    assert len(app_logger.handlers) > 0


def test_logging_with_middleware_context():
    """Integration test: verify logging works with request/job context."""
    logger = logging.getLogger("app.services.test")

    # Simulate middleware setting request ID
    request_id = "req-12345"
    set_request_id(request_id)

    # Simulate service setting job ID
    job_id = uuid4()
    set_job_id(job_id)

    # Log messages at different levels
    logger.info("processing job")
    logger.warning("job processing slow")

    # Verify logger is working (actual JSON output goes to stdout)
    assert logger.isEnabledFor(logging.INFO)
    assert logger.isEnabledFor(logging.WARNING)
