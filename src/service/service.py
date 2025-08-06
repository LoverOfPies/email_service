import os
from asyncio import sleep
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession

from src.app_logger import app_logger
from src.database.models.email_data import EmailData, StatusType
from src.database.postgres import SessionManager
from src.database.rabbit import MessageInfo, RabbitMessageProcessor
from src.service.email_sender import send_email_with_retries
from src.settings.app import settings

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)

def date_filter(value, format_string):
    if isinstance(value, datetime):
        return value.strftime(format_string)
    return value

env.filters['date'] = date_filter


def get_base_context():
    image_url = "%semails/{name}" % (settings.s3_url,)
    return {
        "anonymous_img": image_url.format(name="anon.png"),
        "media_url": f"{settings.s3_url}media/",
    }


async def generate_body(template: str | None, context: dict | None) -> str | None:
    if not template:
        return None
    full_ctx = get_base_context()
    if context:
        full_ctx.update(context)
    template = env.get_template(template)
    return template.render(full_ctx)


class Service:
    def __init__(
        self, session_manager: SessionManager, rabbit_processor: RabbitMessageProcessor
    ):
        self.session_manager = session_manager
        self.rabbit = rabbit_processor

    @staticmethod
    async def process_message(session: AsyncSession, message_info: MessageInfo):
        email_data = message_info.message
        body = await generate_body(email_data.template, email_data.context)
        record = EmailData(
            address=email_data.to,
            subject=email_data.subject,
            template=email_data.template,
            context=email_data.context,
            body=body,
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
