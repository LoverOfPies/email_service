import asyncio

from src.app_logger import app_logger
from src.database.rabbit import get_rabbit_processor
from src.service.service import Service
from src.database.postgres import SessionManager
from src.settings.app import settings


async def main():
    app_logger.info("Запуск сервиса")
    session_manager = SessionManager(settings.postgres)
    async with get_rabbit_processor(settings.rabbit) as rabbit_processor:
        await Service(session_manager, rabbit_processor).run()


if __name__ == "__main__":
    asyncio.run(main())
