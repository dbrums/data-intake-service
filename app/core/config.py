from enum import StrEnum
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "data-intake-service"
    ENV: Environment = Environment.LOCAL
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite:///./data_intake.db"
    LOG_LEVEL: str = "INFO"

    @model_validator(mode="after")
    def validate_production_settings(self) -> Self:
        if self.ENV == Environment.PRODUCTION:
            if self.DEBUG:
                raise ValueError("DEBUG must not be enabled in production")
            if "sqlite" in self.DATABASE_URL:
                raise ValueError("SQLite must not be used in production")
        return self


settings = Settings()
