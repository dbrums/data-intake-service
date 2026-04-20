import logging.config
from pathlib import Path

import yaml


def _find_project_root() -> Path:
    """Find project root by looking for logging_config.yaml."""
    current = Path(__file__).resolve()
    for parent in [current.parent] + list(current.parents):
        config_file = parent / "logging_config.yaml"
        if config_file.exists():
            return config_file
    raise FileNotFoundError("Could not find logging_config.yaml in project tree")


def setup_logging() -> None:
    from app.core.config import settings

    with open(_find_project_root()) as f:
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
