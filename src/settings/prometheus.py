from prometheus_client import Histogram
from pydantic_settings import BaseSettings, SettingsConfigDict


class PrometheusMetrics:
    handle_message_duration = Histogram(
        name="handle_message_duration",
        documentation="Время обработки одного сообщения",
    )


class PrometheusSettings(BaseSettings):
    port: int = 9105
    endpoint: str = "/metrics"
    metrics: PrometheusMetrics = PrometheusMetrics()

    model_config = SettingsConfigDict(env_prefix="EMAIL_SERVICE_PROMETHEUS_", case_sensitive=False)
