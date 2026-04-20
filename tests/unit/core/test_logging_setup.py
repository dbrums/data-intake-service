import logging
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from app.core.logging.setup import (
    _find_project_root,  # type: ignore[reportPrivateUsage]
    setup_logging,
)

if TYPE_CHECKING:
    from pytest import MonkeyPatch


def test_find_project_root_succeeds() -> None:
    """Verify _find_project_root locates logging_config.yaml."""
    config_path = _find_project_root()
    assert config_path.exists()
    assert config_path.name == "logging_config.yaml"


def test_find_project_root_fails_when_missing(tmp_path: Path) -> None:
    """Verify _find_project_root raises when config not found."""
    # Create a temporary module file in a directory without logging_config.yaml
    fake_module = tmp_path / "fake_module.py"
    fake_module.write_text("# fake module")

    # Monkey patch __file__ to point to our fake module
    with patch("app.core.logging.setup.Path") as mock_path:
        mock_path.return_value.resolve.return_value.parents = [
            tmp_path,
            tmp_path.parent,
        ]
        mock_path.return_value.resolve.return_value.parent = tmp_path

        with pytest.raises(
            FileNotFoundError, match="Could not find logging_config.yaml"
        ):
            _find_project_root()


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
