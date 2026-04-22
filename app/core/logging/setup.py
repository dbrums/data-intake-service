import logging.config
from pathlib import Path

import yaml


def _get_logging_config_path() -> Path:
    """Get path to logging configuration file in app/core directory."""
    config_path = Path(__file__).resolve().parent.parent / "logging_config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Logging config not found at {config_path}. "
            "Expected app/core/logging_config.yaml"
        )
    return config_path


def setup_logging() -> None:
    from app.core.config import settings

    with open(_get_logging_config_path()) as f:
        config = yaml.safe_load(f)

    # Override log levels from settings/environment
    log_level = settings.LOG_LEVEL.upper()

    # Set level for handlers
    for handler in config.get("handlers", {}).values():
        if "level" in handler:
            handler["level"] = log_level

    # Set level for app logger
    if "loggers" in config and "app" in config["loggers"]:
        config["loggers"]["app"]["level"] = log_level

    # Set level for root logger
    if "root" in config:
        config["root"]["level"] = log_level

    logging.config.dictConfig(config)
