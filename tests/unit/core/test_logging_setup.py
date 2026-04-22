import logging
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from app.core.logging.setup import (
    _get_logging_config_path,  # type: ignore[reportPrivateUsage]
    setup_logging,
)

if TYPE_CHECKING:
    from pytest import MonkeyPatch


def test_get_logging_config_path_succeeds() -> None:
    """Verify _get_logging_config_path locates logging_config.yaml in app/core."""
    config_path = _get_logging_config_path()
    assert config_path.exists()
    assert config_path.name == "logging_config.yaml"
    assert config_path.parent.name == "core"


def test_get_logging_config_path_fails_when_missing(tmp_path: Path) -> None:
    """Verify _get_logging_config_path raises when config not found."""
    # Create a fake setup.py in a temp directory structure
    fake_logging_dir = tmp_path / "app" / "core" / "logging"
    fake_logging_dir.mkdir(parents=True)
    fake_setup = fake_logging_dir / "setup.py"
    fake_setup.write_text("# fake setup")

    # Monkey patch __file__ to point to our fake module
    with patch("app.core.logging.setup.Path") as mock_path:
        # Mock Path(__file__).resolve().parent.parent to point to tmp app/core
        mock_resolved = mock_path.return_value.resolve.return_value
        mock_resolved.parent.parent = tmp_path / "app" / "core"

        with pytest.raises(
            FileNotFoundError,
            match="Logging config not found.*app/core/logging_config.yaml",
        ):
            _get_logging_config_path()


def test_setup_logging_succeeds() -> None:
    """Verify setup_logging configures logging without error."""
    # Clear any existing configuration
    logging.root.handlers.clear()

    setup_logging()

    # Verify root logger has handlers
    assert len(logging.root.handlers) > 0


def test_setup_logging_respects_log_level_env_var(monkeypatch: "MonkeyPatch") -> None:
    """Verify LOG_LEVEL env var overrides YAML config."""
    # Set LOG_LEVEL to DEBUG
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    # Reload settings to pick up env var
    from importlib import reload

    from app.core import config

    reload(config)

    logging.root.handlers.clear()
    setup_logging()

    # Check that app logger level is DEBUG
    app_logger = logging.getLogger("app")
    assert app_logger.level == logging.DEBUG

    # Cleanup - reset to default
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    reload(config)


def test_setup_logging_sets_handler_levels() -> None:
    """Verify setup_logging sets handler levels from settings."""
    logging.root.handlers.clear()
    setup_logging()

    # Verify console handler has correct level
    root_logger = logging.getLogger()
    handlers = [  # type: ignore[var-annotated]
        h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)
    ]
    assert len(handlers) > 0  # type: ignore[arg-type]
    # Default is INFO from settings
    assert handlers[0].level == logging.INFO


def test_setup_logging_configures_json_formatter() -> None:
    """Verify setup_logging configures JSON formatter."""
    logging.root.handlers.clear()
    setup_logging()

    # Get console handler
    root_logger = logging.getLogger()
    handlers = [  # type: ignore[var-annotated]
        h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)
    ]
    assert len(handlers) > 0  # type: ignore[arg-type]

    # Verify formatter is configured
    formatter = handlers[0].formatter
    assert formatter is not None
    # JsonFormatter should have specific format string
    assert hasattr(formatter, "_fmt")


def test_setup_logging_adds_context_filter() -> None:
    """Verify setup_logging adds ContextFilter to handlers."""
    from app.core.logging.context import ContextFilter

    logging.root.handlers.clear()
    setup_logging()

    # Get console handler
    root_logger = logging.getLogger()
    handlers = [  # type: ignore[var-annotated]
        h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)
    ]
    assert len(handlers) > 0  # type: ignore[arg-type]

    # Verify filter is attached
    filters = handlers[0].filters
    assert any(isinstance(f, ContextFilter) for f in filters)
