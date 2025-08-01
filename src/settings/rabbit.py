from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from aio_pika import ExchangeType
from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class QueueConfig(BaseModel):
    name: str = "email_service"
    durable: bool = True
    exclusive: bool = False
    auto_delete: bool = False
    x_message_ttl: int = 60000


class ExchangeConfig(BaseModel):
    name: str
    type: ExchangeType = ExchangeType.DIRECT
    durable: bool = True
    auto_delete: bool = False


class BindingConfig(BaseModel):
    queue: str
    exchange: str
    routing_key: str = ""
    arguments: dict[str, Any] = Field(default_factory=dict)


class RabbitSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: SecretStr = SecretStr("guest")
    virtual_host: str = "/"

    heartbeat: int = 60  # секунды
    connection_timeout: int = 10  # секунды
    prefetch_count: int = 10
    batch_size: int = 50
    timeout_seconds: float = 1.0
    max_retries: int = 5
    retry_delay_seconds: int = 1

    queue: QueueConfig = Field(default_factory=lambda: QueueConfig(name="email_service"))
    exchange: ExchangeConfig | None = None
    bindings: list[BindingConfig] = Field(default_factory=list)

    model_config = SettingsConfigDict(env_prefix="EMAIL_SERVICE_RABBIT_")

    @field_validator("port", "heartbeat", "connection_timeout")
    def validate_positive_ints(cls, v):
        if v <= 0:
            raise ValueError("Value must be positive integer")
        return v

    @model_validator(mode="after")
    def setup_default_binding(self):
        if not self.bindings:
            self.bindings = [
                BindingConfig(
                    queue=self.queue.name,
                    exchange=self.exchange.name,
                    routing_key="email.*"
                )
            ]
        return self

    @property
    def amqp_url(self) -> str:
        base = (
            f"amqp://{self.username}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.virtual_host}"
            f"?heartbeat={self.heartbeat}&connection_timeout={self.connection_timeout}"
        )
        params = {
            "heartbeat": self.heartbeat,
            "connection_timeout": self.connection_timeout,
            "ssl": True,
            "ssl_options": {"ca_certs": ...},
        }
        return f"{base}?{urlencode(params)}"
