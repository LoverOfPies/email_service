import logging

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from settings.postgres import PostgresSettings
from settings.rabbit import RabbitSettings
from src.settings.prometheus import PrometheusSettings


class Settings(BaseSettings):
    log_level: str = Field(
        default="WARNING",
        description=f"One of {', '.join(logging._nameToLevel.copy())}",
    )

    rabbit: RabbitSettings = RabbitSettings()
    postgres: PostgresSettings = PostgresSettings()
    prometheus: PrometheusSettings = PrometheusSettings()

    @field_validator("log_level", mode="before")
    def validate_log_level(cls, v: str) -> str:
        if v not in logging._nameToLevel.copy():
            raise ValueError("Error log level")
        return v

    model_config = SettingsConfigDict(env_prefix="EMAIL_SERVICE_", case_sensitive=False)


settings = Settings()
