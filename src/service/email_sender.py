import asyncio
import base64
import mimetypes
import smtplib
from email.message import EmailMessage
from asyncio import sleep

from sqlalchemy.ext.asyncio import AsyncSession

from src.app_logger import app_logger
from src.database.models.email_data import StatusType, EmailData
from src.settings.app import settings


async def _send_email_sync(
    to: str,
    subject: str,
    message: str | None,
    body: str | None,
    attachments: list | None,
):
    msg = EmailMessage()
    msg["From"] = settings.email_from
    msg["To"] = to
    msg["Subject"] = subject

    if message:
        msg.set_content(message)
    if body:
        msg.add_alternative(body, subtype="html")

    if attachments:
        for attachment in attachments:
            file_data = base64.b64decode(attachment["content"])
            file_name = attachment["filename"]
            mime_type, _ = mimetypes.guess_type(file_name)
            mime_type = mime_type or "application/octet-stream"
            main_type, sub_type = mime_type.split("/", 1)
            msg.add_attachment(
                file_data,
                maintype=main_type,
                subtype=sub_type,
                filename=file_name,
            )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(
            settings.smtp_user,
            settings.smtp_password.get_secret_value(),
        )
        server.send_message(msg)


async def send_email_with_retries(
    session: AsyncSession, email_id: int, max_retries: int = 3, retry_delay: int = 5
):
    for attempt in range(max_retries + 1):
        try:
            record = await session.get(EmailData, email_id, with_for_update=True)
            if not record:
                app_logger.error(f"Запись email {email_id} не найдена")
                return

            if record.status not in {StatusType.NEW, StatusType.RETRY}:
                app_logger.info(f"Пропуск email {email_id}, статус: {record.status}")
                return

            record.status = StatusType.PROCESSING
            record.error = None
            await session.flush()

            await asyncio.to_thread(
                _send_email_sync,
                to=record.address,
                subject=record.subject,
                message=record.message,
                body=record.body,
                attachments=record.attachments,
            )

            record.status = StatusType.PROCESSED
            app_logger.info(f"Письмо {email_id} успешно отправлено")
            return

        except smtplib.SMTPException as e:
            app_logger.warning(
                f"Попытка {attempt+1}/{max_retries} отправки {email_id} не удалась: {str(e)}"
            )
            record = await session.get(EmailData, email_id, with_for_update=True)

            if attempt < max_retries:
                record.status = StatusType.RETRY
                record.error = str(e)
                await sleep(retry_delay * (2**attempt))
            else:
                record.status = StatusType.ERROR
                record.error = str(e)
                app_logger.error(
                    f"Письмо {email_id} не отправлено после {max_retries} попыток"
                )
                return

        except Exception as e:
            record = await session.get(EmailData, email_id, with_for_update=True)
            record.status = StatusType.ERROR
            record.error = str(e)
            app_logger.error(f"Неустранимая ошибка при отправке {email_id}: {str(e)}")
            return
