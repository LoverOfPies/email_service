from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from aio_pika import ExchangeType


class QueueConfig(BaseModel):
    name: str = "email_service"
    durable: bool = True
    exclusive: bool = False
    auto_delete: bool = False
    x_message_ttl: int = 60000
    dead_letter_exchange: str = "dlx.email"
    dead_letter_routing_key: str = "failed_emails"


class ExchangeConfig(BaseModel):
    name: str
    type: ExchangeType = ExchangeType.DIRECT
    durable: bool = True
    auto_delete: bool = False


class BindingConfig(BaseModel):
    routing_key: str = ""
    arguments: dict[str, Any] = Field(default_factory=dict)


class RabbitSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: SecretStr = SecretStr("guest")
    virtual_host: str = "/"

    use_ssl: bool = False
    ca_certs: str | None = None
    certfile: str | None = None
    keyfile: str | None = None

    heartbeat: int = 60
    connection_timeout: int = 10
    prefetch_count: int = 10
    batch_size: int = 50
    timeout_seconds: float = 1.0
    max_retries: int = 5
    retry_delay_seconds: int = 1

    queue: QueueConfig = Field(
        default_factory=lambda: QueueConfig(name="email_service")
    )
    exchange: ExchangeConfig | None = None
    bindings: list[BindingConfig] = Field(default_factory=list)

    model_config = SettingsConfigDict(env_prefix="EMAIL_SERVICE_RABBIT_")

    @field_validator(
        "port",
        "heartbeat",
        "connection_timeout",
        "prefetch_count",
        "batch_size",
        "timeout_seconds",
        "max_retries",
        "retry_delay_seconds",
    )
    def validate_positive_ints(cls, v):
        if v <= 0:
            raise ValueError("Значение должно быть положительным числом")
        return v

    @model_validator(mode="after")
    def setup_default_binding(self):
        if not self.bindings and self.exchange:
            self.bindings = [BindingConfig(routing_key="email.*")]
        return self
