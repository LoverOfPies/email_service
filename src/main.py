import asyncio
import logging

from service.service import Service

logging.basicConfig(level=logging.INFO)


async def main():
    logging.info("Starting email service")
    await Service(postgres, rabbit).run()


if __name__ == "__main__":
    asyncio.run(main())
