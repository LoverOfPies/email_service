from asyncio import sleep

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.rabbit import RabbitMessageProcessor
from src.settings.app import settings
from src.database.postgres import SessionManager


class Service:

    def __init__(self, session_manager: SessionManager, rabbit_processor: RabbitMessageProcessor):
        self.session_manager = session_manager
        self.rabbit = rabbit_processor

    async def process_message(self, session: AsyncSession):
        ...

    async def run(self):
        while True:
            # Сервис не сильно нагруженный, поэтому можем простаивать
            await sleep(settings.timeout_for_repeat_read)
            messages = await rabbit_processor
            for msg in messages:
                async with self.session_manager() as session:
                    await self.process_message(
                        session,
                    )
