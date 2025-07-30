from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    engine: str = "postgresql+psycopg"
    dbname: str = "boardingdb"
    host: str = "localhost"
    port: int = 5434
    user: str = "postgres"
    password: SecretStr = SecretStr("admin")
    default_schema: str = "emails"

    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 1800
    pool_timeout: int = 30
    pool_pre_ping: bool = True

    autocommit: bool = False
    autoflush: bool = False

    model_config = SettingsConfigDict(
        env_prefix="EMAIL_SERVICE_POSTGRES_", case_sensitive=False
    )

    @property
    def dsn(self) -> str:
        return (
            f"{self.engine}://{self.user}:{self.password.get_secret_value()}@"
            f"{self.host}:{self.port}/{self.dbname}"
        )
