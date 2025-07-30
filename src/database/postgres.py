from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Self

from service.app_logger import app_logger
from src.settings.postgres import PostgresSettings


def handle_db_exceptions(fn):
    @wraps(fn)
    async def async_wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except psycopg.Error as e:
            app_logger.error("POSTGRES_OPERATION_FAILED", e=e)
            raise
        except Exception as e:
            app_logger.error("POSTGRES_ERROR", e=e)
            raise Exception from e

    return async_wrapper


class BasePostgresConnectionManager(ABC):
    @abstractmethod
    async def __aenter__(self) -> Self:
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    @abstractmethod
    async def get_connection(self) -> AsyncConnection:
        pass


class PostgresConnectionManager:
    def __init__(self, settings: PostgresSettings) -> None:
        self.settings: PostgresSettings = settings
        self._connection: AsyncConnection | None = None

    async def __aenter__(self) -> Self:
        await self._init_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._connection.close()

    async def get_connection(self) -> AsyncConnection:
        if not self._connection or self._connection.closed:
            await self._init_connection()
        return self._connection

    async def _init_connection(self) -> None:
        app_logger.error(
            "POSTGRES_CONNECT",
            dbname=self.settings.dbname,
            host=self.settings.host,
            port=self.settings.port,
        )
        self._connection: AsyncConnection = await AsyncConnection.connect(
            **self.settings.config
        )
        query = sql.SQL("SET search_path TO {}").format(
            sql.Identifier(self.settings.default_schema)
        )
        await self._connection.execute(query)


class PostgresUnitOfWork:
    def __init__(self, connection_manager: PostgresConnectionManager) -> None:
        self._connection_manager: PostgresConnectionManager = connection_manager

    async def __aenter__(self) -> Self:
        connection: AsyncConnection = await self._connection_manager.get_connection()
        self._cursor = connection.cursor()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

        await self._cursor.close()
        self._cursor = None
        self._connection_manager = None

    @handle_db_exceptions
    async def commit(self) -> None:
        connection: AsyncConnection = await self._connection_manager.get_connection()
        await connection.commit()

    @handle_db_exceptions
    async def rollback(self) -> None:
        connection: AsyncConnection = await self._connection_manager.get_connection()
        app_logger.error("POSTGRES_ROLLBACK")
        await connection.rollback()

    @handle_db_exceptions
    async def insert(self, table: str, data: dict[str, Any]) -> None:
        columns = data.keys()
        query = sql.SQL(
            "INSERT INTO {schema}.{table} ({fields}) VALUES ({values})"
        ).format(
            schema=sql.Identifier(self._connection_manager.settings.default_schema),
            table=sql.Identifier(table),
            fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
            values=sql.SQL(", ").join(map(sql.Placeholder, columns)),
        )
        await self._cursor.execute(query, data)

    @handle_db_exceptions
    async def select(
        self,
        table: str,
        columns: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        query = sql.SQL("SELECT {cols} FROM {schema}.{table}").format(
            cols=(
                sql.SQL(", ").join(map(sql.Identifier, columns))
                if columns
                else sql.SQL("*")
            ),
            schema=sql.Identifier(self._connection_manager.settings.default_schema),
            table=sql.Identifier(table),
        )
        if where:
            conditions = sql.SQL(" AND ").join(
                sql.SQL("{col} = {val}").format(
                    col=sql.Identifier(col), val=sql.Placeholder(col)
                )
                for col in where.keys()
            )
            query = sql.SQL("{query} WHERE {cond}").format(query=query, cond=conditions)
        await self._cursor.execute(query, where or {})
        result = await self._cursor.fetchall()
        columns = [desc[0] for desc in self._cursor.description]
        result = [dict(zip(columns, row)) for row in result]

        return result

    @handle_db_exceptions
    async def update(
        self, table: str, data: dict[str, Any], where: dict[str, Any]
    ) -> None:
        common_keys = set(data.keys()) & set(where.keys())
        if common_keys:
            raise ValueError(
                f"Conflicting keys in data and where: {', '.join(common_keys)}"
            )

        set_clause = sql.SQL(", ").join(
            sql.SQL("{col} = {val}").format(
                col=sql.Identifier(col), val=sql.Placeholder(col)
            )
            for col in data.keys()
        )
        where_clause = sql.SQL(" AND ").join(
            sql.SQL("{col} = {val}").format(
                col=sql.Identifier(col), val=sql.Placeholder(col)
            )
            for col in where.keys()
        )

        query = sql.SQL(
            "UPDATE {schema}.{table} SET {set_clause} WHERE {where_clause}"
        ).format(
            schema=sql.Identifier(self._connection_manager.settings.default_schema),
            table=sql.Identifier(table),
            set_clause=set_clause,
            where_clause=where_clause,
        )
        await self._cursor.execute(query, {**data, **where})

    async def delete(self, table: str, where: dict[str, Any]) -> None:
        where_clause = sql.SQL(" AND ").join(
            sql.SQL("{col} = {val}").format(
                col=sql.Identifier(col), val=sql.Placeholder(col)
            )
            for col in where.keys()
        )
        query = sql.SQL("DELETE FROM {schema}.{table} WHERE {where_clause}").format(
            schema=sql.Identifier(self._connection_manager.settings.default_schema),
            table=sql.Identifier(table),
            where_clause=where_clause,
        )
        await self._cursor.execute(query, where or {})
