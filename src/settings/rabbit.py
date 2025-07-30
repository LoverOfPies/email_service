from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExchangeType(str, Enum):
    """Типы RabbitMQ exchange"""
    DIRECT = "direct"
    FANOUT = "fanout"
    TOPIC = "topic"
    HEADERS = "headers"


class QueueConfig(BaseModel):
    """Конфигурация очереди RabbitMQ"""
    name: str
    durable: bool = True
    exclusive: bool = False
    auto_delete: bool = False
    arguments: dict[str, Any] = Field(default_factory=dict)


class ExchangeConfig(BaseModel):
    """Конфигурация exchange RabbitMQ"""
    name: str
    type: ExchangeType = ExchangeType.DIRECT
    durable: bool = True
    auto_delete: bool = False


class BindingConfig(BaseModel):
    """Конфигурация привязки очереди к exchange"""
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
    queue: QueueConfig = Field(default_factory=lambda: QueueConfig(name="email_service"))
    exchange: ExchangeConfig = Field(default_factory=lambda: ExchangeConfig(
        name="email_exchange",
        type=ExchangeType.TOPIC
    ))
    bindings: list[BindingConfig] = Field(default_factory=list)

    model_config = SettingsConfigDict(env_prefix="EMAIL_SERVICE_RABBIT_")

    @field_validator("port", "heartbeat", "connection_timeout")
    def validate_positive_ints(cls, v):
        """Проверка положительных целых значений"""
        if v <= 0:
            raise ValueError("Value must be positive integer")
        return v

    @model_validator(mode="after")
    def setup_default_binding(self):
        """Автоматическое создание дефолтной привязки, если не указано"""
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
        """Генерация AMQP URL для подключения"""
        return (
            f"amqp://{self.username}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.virtual_host}"
            f"?heartbeat={self.heartbeat}&connection_timeout={self.connection_timeout}"
        )
