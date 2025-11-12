"""
API Gateway Database Models
"""
from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
import uuid

Base = declarative_base()


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    notification_type = Column(String, nullable=False)  # 'email' or 'push'
    template_code = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # 'pending', 'delivered', 'failed'
    priority = Column(Integer, default=5)
    notification_metadata = Column("metadata", JSONB, nullable=True)  # Column name in DB is 'metadata', but attribute is renamed to avoid SQLAlchemy conflict
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NotificationCreate(BaseModel):
    user_id: str
    notification_type: str
    template_code: str
    priority: int = 5
    metadata: Optional[dict] = None

