import logging

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.settings.postgres import PostgresSettings
from src.settings.prometheus import PrometheusSettings
from src.settings.rabbit import RabbitSettings


class Settings(BaseSettings):
    log_level: str = Field(
        default="WARNING",
        description=f"One of {', '.join(logging._nameToLevel.copy())}",
    )
    timeout_for_repeat_read: int = 30

    s3_url: str = "https://your-s3-endpoint/"
    base_url: str = "https://base.com/"
    facebook_url: str = "https://facebook.com/me"
    instagram_url: str = "https://instagram.com/me"

    email_from: str = "ilya.408@yandex.ru>"
    smtp_password: SecretStr = SecretStr("password")
    smtp_user: str = "ff"
    smtp_host: str = 'smtp.zeptomail.com'
    smtp_port: int = 587

    rabbit: RabbitSettings = RabbitSettings()
    postgres: PostgresSettings = PostgresSettings()
    prometheus: PrometheusSettings = PrometheusSettings()

    @field_validator("log_level", mode="before")
    def validate_log_level(cls, v: str) -> str:
        if v not in logging._nameToLevel.copy():
            raise ValueError("Неправильный уровень логов")
        return v

    model_config = SettingsConfigDict(env_prefix="EMAIL_SERVICE_", case_sensitive=False)


settings = Settings()
