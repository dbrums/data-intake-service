"""Unit tests for worker tasks."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas.job import JobFail
from app.workers.tasks import execute_validation_job


class TestExecuteValidationJob:
    """Test the execute_validation_job worker task."""

    @patch("app.workers.tasks.SessionLocal")
    @patch("app.workers.tasks.SqlAlchemyJobRepository")
    @patch("app.workers.tasks.JobService")
    @patch("app.workers.tasks.set_job_id")
    @patch("app.workers.tasks.sleep")
    def test_successful_job_execution(
        self,
        mock_sleep: MagicMock,
        mock_set_job_id: MagicMock,
        mock_job_service_class: MagicMock,
        mock_repo_class: MagicMock,
        mock_session_local: MagicMock,
    ):
        """Test successful job execution path."""
        # Arrange
        job_id = uuid4()
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_job_service_class.return_value = mock_service

        # Act
        execute_validation_job(job_id)

        # Assert
        mock_session_local.assert_called_once()
        mock_repo_class.assert_called_once_with(mock_db)
        mock_job_service_class.assert_called_once_with(mock_repo)
        mock_set_job_id.assert_called_once_with(job_id)
        mock_service.start_job.assert_called_once_with(job_id)
        mock_sleep.assert_called_once_with(3)
        mock_service.complete_job.assert_called_once_with(job_id)
        mock_db.close.assert_called_once()

    @patch("app.workers.tasks.SessionLocal")
    @patch("app.workers.tasks.SqlAlchemyJobRepository")
    @patch("app.workers.tasks.JobService")
    @patch("app.workers.tasks.set_job_id")
    @patch("app.workers.tasks.sleep")
    def test_job_failure_during_execution(
        self,
        mock_sleep: MagicMock,
        mock_set_job_id: MagicMock,
        mock_job_service_class: MagicMock,
        mock_repo_class: MagicMock,
        mock_session_local: MagicMock,
    ):
        """Test job failure handling when work raises exception."""
        # Arrange
        job_id = uuid4()
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_job_service_class.return_value = mock_service

        # Simulate failure during validation
        mock_sleep.side_effect = Exception("Validation failed")

        # Act & Assert
        with pytest.raises(Exception, match="Validation failed"):
            execute_validation_job(job_id)

        # Verify fail_job was called
        mock_service.fail_job.assert_called_once()
        call_args = mock_service.fail_job.call_args
        fail_payload = call_args[0][0]
        assert isinstance(fail_payload, JobFail)
        assert fail_payload.error_code == "WORKER_ERROR"
        assert "Validation failed" in fail_payload.error_message
        assert call_args[0][1] == job_id

        # Verify cleanup
        mock_db.close.assert_called_once()

    @patch("app.workers.tasks.SessionLocal")
    @patch("app.workers.tasks.SqlAlchemyJobRepository")
    def test_failure_before_service_creation(
        self,
        mock_repo_class: MagicMock,
        mock_session_local: MagicMock,
    ):
        """Test that service failure is handled when service is None."""
        # Arrange
        job_id = uuid4()
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Simulate failure during repository creation
        mock_repo_class.side_effect = Exception("DB connection failed")

        # Act & Assert
        with pytest.raises(Exception, match="DB connection failed"):
            execute_validation_job(job_id)

        # Service was never created, so fail_job should not be called
        # But DB should still be closed
        mock_db.close.assert_called_once()

    @patch("app.workers.tasks.SessionLocal")
    @patch("app.workers.tasks.SqlAlchemyJobRepository")
    @patch("app.workers.tasks.JobService")
    @patch("app.workers.tasks.set_job_id")
    def test_error_message_truncation(
        self,
        mock_set_job_id: MagicMock,
        mock_job_service_class: MagicMock,
        mock_repo_class: MagicMock,
        mock_session_local: MagicMock,
    ):
        """Test that error messages are truncated to 500 characters."""
        # Arrange
        job_id = uuid4()
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_job_service_class.return_value = mock_service

        # Simulate failure with very long error message
        long_error = "x" * 600
        test_exception = Exception(long_error)
        mock_service.start_job.side_effect = test_exception

        # Act & Assert
        with pytest.raises(Exception, match="x+"):
            execute_validation_job(job_id)

        # Verify error message was truncated
        mock_service.fail_job.assert_called_once()
        fail_payload = mock_service.fail_job.call_args[0][0]
        assert len(fail_payload.error_message) == 500
        assert fail_payload.error_message == long_error[:500]
