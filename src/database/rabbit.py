import asyncio
import json
from typing import AsyncGenerator, Any
from contextlib import asynccontextmanager
import aio_pika
from aiormq import AMQPError
from pydantic import BaseModel
import ssl

from src.app_logger import app_logger
from src.settings.rabbit import RabbitSettings


class RabbitMessageMeta(BaseModel):
    exchange: str | None = None
    routing_key: str | None = None
    delivery_tag: int | None = None

    def __str__(self) -> str:
        return (
            f"Exchange: {self.exchange}, "
            f"Routing Key: {self.routing_key}, "
            f"Delivery Tag: {self.delivery_tag}"
        )


class MessageInfo(BaseModel):
    message: dict[str, Any]
    message_meta: RabbitMessageMeta


class RabbitConnection:
    def __init__(self, settings: RabbitSettings) -> None:
        self.settings = settings
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.abc.AbstractRobustChannel | None = None
        self.queue: aio_pika.abc.AbstractRobustQueue | None = None
        self.exchange: aio_pika.abc.AbstractRobustExchange | None = None

    async def connect(self) -> None:
        app_logger.info("Подключение к RabbitMQ")
        try:
            if self.settings.use_ssl:
                context = ssl.create_default_context(cafile=self.settings.ca_certs)
                if self.settings.certfile and self.settings.keyfile:
                    context.load_cert_chain(
                        certfile=self.settings.certfile, keyfile=self.settings.keyfile
                    )
            else:
                context = False

            self.connection = await aio_pika.connect_robust(
                host=self.settings.host,
                port=self.settings.port,
                login=self.settings.username,
                password=self.settings.password.get_secret_value(),
                virtualhost=self.settings.virtual_host,
                ssl=context,
            )

            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.settings.prefetch_count)

            if self.settings.exchange:
                self.exchange = await self.channel.declare_exchange(
                    name=self.settings.exchange.name,
                    type=self.settings.exchange.type,
                    durable=self.settings.exchange.durable,
                    auto_delete=self.settings.exchange.auto_delete,
                )

            self.queue = await self.channel.declare_queue(
                name=self.settings.queue.name,
                durable=self.settings.queue.durable,
                exclusive=self.settings.queue.exclusive,
                auto_delete=self.settings.queue.auto_delete,
                arguments={
                    "x-message-ttl": self.settings.queue.x_message_ttl,
                    "x-dead-letter-exchange": self.settings.queue.dead_letter_exchange,
                    "x-dead-letter-routing-key": self.settings.queue.dead_letter_routing_key,
                },
            )

            if self.exchange:
                for binding in self.settings.bindings:
                    await self.queue.bind(
                        exchange=self.exchange,
                        routing_key=binding.routing_key,
                        arguments=binding.arguments,
                    )

            app_logger.info("Подключение к RabbitMQ установлено")
        except Exception as e:
            app_logger.error(f"Ошибка при подключении к RabbitMQ: {e}")
            await self.close()
            raise

    async def close(self) -> None:
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        app_logger.info("Подключение к RabbitMQ закрыто")


class RabbitReader:
    def __init__(self, settings: RabbitSettings) -> None:
        self.settings = settings
        self.max_retries = settings.max_retries
        self.retry_delay_seconds = settings.retry_delay_seconds
        self._connection_manager = RabbitConnection(settings)

    async def _get_connection(self) -> RabbitConnection:
        if not self._connection_manager.connection:
            await self._connection_manager.connect()
        return self._connection_manager

    async def reset(self) -> None:
        await self._connection_manager.close()
        await self._connection_manager.connect()

    async def close(self) -> None:
        await self._connection_manager.close()

    @staticmethod
    def decode_message(rabbit_message: aio_pika.IncomingMessage) -> MessageInfo:
        message_meta = RabbitMessageMeta(
            exchange=rabbit_message.exchange,
            routing_key=rabbit_message.routing_key,
            delivery_tag=rabbit_message.delivery_tag,
        )
        try:
            message = json.loads(rabbit_message.body.decode())
        except json.JSONDecodeError:
            message = {}
            app_logger.error(
                f"Ошибка при декодирования сообщения из RabbitMQ. {message_meta}"
            )
        return MessageInfo(message=message, message_meta=message_meta)

    async def read(self) -> list[aio_pika.IncomingMessage]:
        conn = await self._get_connection()
        messages = []
        start_time = asyncio.get_running_loop().time()
        timeout = self.settings.timeout_seconds

        while len(messages) < self.settings.batch_size:
            elapsed = asyncio.get_running_loop().time() - start_time
            remaining_time = max(0.0, timeout - elapsed)

            if remaining_time <= 0:
                break

            try:
                message = await asyncio.wait_for(
                    conn.queue.get(fail=False), remaining_time
                )
                if message:
                    messages.append(message)
            except asyncio.TimeoutError:
                break

        app_logger.info(f"Прочитано {len(messages)} сообщений из RabbitMQ")
        return messages


@asynccontextmanager
async def get_rabbit_processor(
    settings: RabbitSettings,
) -> AsyncGenerator["RabbitMessageProcessor", None]:
    reader = RabbitReader(settings)
    processor = RabbitMessageProcessor(reader)
    try:
        yield processor
    finally:
        await processor.close()


class RabbitMessageProcessor:
    def __init__(self, rabbit_reader: RabbitReader):
        self.reader = rabbit_reader
        self.messages: list[aio_pika.IncomingMessage] = []

    async def __aenter__(self) -> list[MessageInfo]:
        max_retries = self.reader.settings.max_retries
        retry_delay = self.reader.settings.retry_delay_seconds

        for attempt in range(max_retries):
            try:
                raw_messages = await self.reader.read()
                self.messages = raw_messages
                decoded_messages = [
                    self.reader.decode_message(msg) for msg in raw_messages
                ]
                return decoded_messages
            except Exception as e:
                if attempt < max_retries - 1:
                    app_logger.error(
                        f"Ошибка при чтении из RabbitMQ. Попытка повторного чтения: {attempt + 1}/{max_retries}"
                    )
                    await asyncio.sleep(retry_delay * (2**attempt))
                    await self.reader.reset()
                else:
                    app_logger.error(f"Ошибка при чтении из RabbitMQ: {e}")
                    raise
        raise AMQPError("Ошибка при чтении из RabbitMQ после нескольких попыток")

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            app_logger.error(
                f"Ошибка при обработки сообщений, {len(self.messages)} отказных сообщений"
            )
            for msg in self.messages:
                await msg.nack()
            await self.reader.reset()
        else:
            app_logger.info(
                f"Успешно обработано {len(self.messages)} сообщений"
            )
            for msg in self.messages:
                await msg.ack()
        self.messages = []

    async def close(self) -> None:
        await self.reader.close()
