import os
import base64
import smtplib
from email.message import EmailMessage

from src.app_logger import app_logger
from src.database.models.email_data import StatusType


async def send_email_instance(record, session):
    try:
        record.status = StatusType.PROCESSING
        session.commit()

        msg = EmailMessage()
        msg['To'] = record.address
        msg['Subject'] = record.subject
        msg.add_alternative(record.body, subtype="html")

        # Обработка вложений
        for attachment in record.attachments:
            file_data = base64.b64decode(attachment['content'])
            msg.add_attachment(
                file_data,
                maintype='application',
                subtype='octet-stream',
                filename=attachment['filename']
            )

        # Отправка через SMTP
        with smtplib.SMTP('smtp.zeptomail.com', 587) as server:
            server.starttls()
            server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
            server.send_message(msg)

        record.status = StatusType.PROCESSED
        session.commit()

    except Exception as e:
        record.status = StatusType.ERROR
        record.error = str(e)
        session.commit()
        app_logger.error(f"Email send error: {str(e)}")
