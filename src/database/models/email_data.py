import enum

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

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
    subject = Column(String(255))
    message = Column(Text, nullable=True)
    template = Column(String(255), nullable=True)
    context = Column(JSONB, nullable=True)
    body = Column(Text, nullable=True)
    status = Column(Enum(StatusType, schema="emails"), default=StatusType.NEW)
    attachments = Column(JSONB, nullable=True)
    created_at = Column(DateTime, server_default="now()")
    error = Column(Text, nullable=True)
