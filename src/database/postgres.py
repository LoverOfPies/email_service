from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from src.app_logger import app_logger
from src.settings.postgres import PostgresSettings


class Base(AsyncAttrs, DeclarativeBase):
    pass


class SessionManager:
    def __init__(self, settings: PostgresSettings | dict) -> None:
        self.settings = settings
        app_logger.info("Подключение к Postgres начато")
        app_logger.debug(self.settings.model_dump_json(indent=4))
        _engine = create_async_engine(
            self.settings.dsn,
            echo=self.settings.echo,
            pool_size=self.settings.pool_size,
            max_overflow=self.settings.max_overflow,
            pool_recycle=self.settings.pool_recycle,
            pool_timeout=self.settings.pool_timeout,
            pool_pre_ping=self.settings.pool_pre_ping,
        )
        self._async_session = async_sessionmaker(
            bind=_engine,
            autocommit = self.settings.autocommit,
        )
        app_logger.info("Подключение к Postgres установлено")

    @asynccontextmanager
    async def __call__(self) -> AsyncGenerator[AsyncSession, None]:
        app_logger.info("Создание сессии Postgres")
        async with self._async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
        app_logger.info("Сессия Postgres создана")
