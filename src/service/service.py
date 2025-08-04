from asyncio import sleep
from sqlalchemy.ext.asyncio import AsyncSession

from src.app_logger import app_logger
from src.database.rabbit import RabbitMessageProcessor, MessageInfo
from src.database.postgres import SessionManager
from src.database.models.email_data import EmailData, StatusType
from src.service.email_sender import send_email_with_retries
from src.settings.app import settings


class Service:
    def __init__(
        self, session_manager: SessionManager, rabbit_processor: RabbitMessageProcessor
    ):
        self.session_manager = session_manager
        self.rabbit = rabbit_processor

    @staticmethod
    async def process_message(session: AsyncSession, message_info: MessageInfo):
        email_data = message_info.message
        record = EmailData(
            address=email_data.to,
            subject=email_data.subject,
            body=email_data.body,
            attachments=email_data.attachments,
            status=StatusType.NEW,
        )
        session.add(record)
        await session.flush()
        await send_email_with_retries(session=session, email_id=record.id)

    async def run(self):
        while True:
            async with self.rabbit as message:
                if not message or not message.message:
                    await sleep(1)
                    continue

                try:
                    async with self.session_manager() as session:
                        await self.process_message(session, message)
                except Exception as e:
                    app_logger.error(f"Ошибка обработки сообщения: {str(e)}")
