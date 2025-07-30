import asyncio
import logging

from src.service.service import Service
from src.database.postgres import SessionManager
from src.settings.app import settings

logging.basicConfig(level=logging.INFO)


async def main():
    logging.info("Starting email service")
    session_manager = SessionManager(settings.postgres)
    rabbit = ...
    await Service(session_manager, rabbit).run()


if __name__ == "__main__":
    asyncio.run(main())
