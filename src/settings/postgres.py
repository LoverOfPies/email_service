from typing import Any

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    dbname: str = "postgres"
    host: str = "localhost"
    port: str = "5432"
    user: str = "postgres"
    password: SecretStr = SecretStr("postgres")
    default_schema: str = "siebel_grhub_buffer"

    model_config = SettingsConfigDict(
        env_prefix="GR_LEGACY_ADAPTER_POSTGRES_", case_sensitive=False
    )

    @property
    def config(self) -> dict[str, Any]:
        postgres_config = {
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password.get_secret_value(),
            "host": self.host,
            "port": self.port,
        }

        return postgres_config
