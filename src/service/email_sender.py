import base64
import mimetypes
import smtplib
from email.message import EmailMessage
from asyncio import sleep

from src.app_logger import app_logger
from src.database.models.email_data import StatusType
from src.settings.app import settings


async def send_email_with_retries(session, record, max_retries=3, retry_delay=5):
    for attempt in range(max_retries):
        try:
            if record.status not in {StatusType.NEW, StatusType.RETRY}:
                app_logger.info(
                    f"Письмо {record.id} в процессе отправки, статус: {record.status}"
                )
                return

            record.status = StatusType.PROCESSING
            await session.commit()

            msg = EmailMessage()
            msg["From"] = settings.email_from
            msg["To"] = record.address
            msg["Subject"] = record.subject
            if record.message:
                msg.set_content(record.message)
            if record.body:
                msg.add_alternative(record.body, subtype="html")

            if record.attachments:
                for attachment in record.attachments:
                    try:
                        file_data = base64.b64decode(attachment["content"])
                        file_name = attachment["filename"]
                        mime_type, _ = mimetypes.guess_type(file_name)
                        if not mime_type:
                            mime_type = "application/octet-stream"
                        main_type, sub_type = mime_type.split("/", 1)
                        msg.add_attachment(
                            file_data,
                            maintype=main_type,
                            subtype=sub_type,
                            filename=file_name,
                        )
                    except Exception as e:
                        app_logger.error(
                            f"Ошибка при добавлении вложения {attachment.get('filename')}: {str(e)}"
                        )

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(
                    settings.smtp_user,
                    settings.smtp_password.get_secret_value(),
                )
                server.send_message(msg)
            record.status = StatusType.PROCESSED
            await session.commit()
            app_logger.info(f"Письмо {record.id} успешно отправлено")
            return

        except smtplib.SMTPException as e:
            app_logger.warning(
                f"Попытка {attempt + 1}/{max_retries} отправки письма {record.id} не удалась: {str(e)}"
            )
            if attempt < max_retries - 1:
                record.status = StatusType.RETRY
                await session.commit()
                await sleep(retry_delay * (2**attempt))
            else:
                record.status = StatusType.ERROR
                app_logger.error(
                    f"Письмо {record.id} не удалось отправить после {max_retries} попыток: {str(e)}"
                )
                await session.commit()
        except Exception as e:
            record.status = StatusType.ERROR
            app_logger.error(
                f"Неустранимая ошибка при отправке письма {record.id}: {str(e)}"
            )
            await session.commit()
            return
