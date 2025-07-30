from sqlalchemy import Column, Integer, String, Text, Enum, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class StatusType(enum.Enum):
    NEW = "new"
    PROCESSED = "processed"
    PROCESSING = "processing"
    ERROR = "error"


class EmailData(Base):
    __tablename__ = 'emaildata'

    id = Column(Integer, primary_key=True)
    address = Column(String(255))
    message = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    subject = Column(String(255))
    status = Column(Enum(StatusType), default=StatusType.NEW)
    attachments = Column(JSON)
    created_at = Column(DateTime, server_default='now()')
    error = Column(Text, nullable=True)
