from sqlalchemy import Column, Integer, String, Text, Enum, JSON, DateTime
import enum

from src.database.postgres import Base


class StatusType(enum.Enum):
    NEW = "new"
    RETRY = "retry"
    PROCESSED = "processed"
    PROCESSING = "processing"
    ERROR = "error"


class EmailData(Base):
    __tablename__ = "email_data"
    __table_args__ = {"schema": "emails"}

    id = Column(Integer, primary_key=True)
    address = Column(String(255))
    message = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    subject = Column(String(255))
    status = Column(Enum(StatusType, schema="emails"), default=StatusType.NEW)
    attachments = Column(JSON)
    created_at = Column(DateTime, server_default="now()")
    error = Column(Text, nullable=True)
