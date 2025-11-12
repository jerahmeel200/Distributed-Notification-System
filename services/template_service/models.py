"""
Template Service Database Models
"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, model_validator
from typing import Optional, Any
from datetime import datetime
import uuid

Base = declarative_base()


class Template(Base):
    __tablename__ = "templates"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    notification_type = Column(String, nullable=False)  # 'email' or 'push'
    language = Column(String, default="en")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Pydantic models
class TemplateCreate(BaseModel):
    code: str
    name: str
    subject: str
    body: str
    notification_type: str
    language: Optional[str] = "en"


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    language: Optional[str] = None


class TemplateResponse(BaseModel):
    id: str
    code: str
    name: str
    subject: str
    body: str
    notification_type: str
    language: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def convert_datetime_fields(cls, data: Any) -> Any:
        """Convert datetime objects to ISO format strings before validation"""
        if isinstance(data, dict):
            if 'created_at' in data and isinstance(data['created_at'], datetime):
                data['created_at'] = data['created_at'].isoformat()
            if 'updated_at' in data and isinstance(data['updated_at'], datetime):
                data['updated_at'] = data['updated_at'].isoformat()
        elif hasattr(data, '__dict__'):
            # Handle ORM objects
            if hasattr(data, 'created_at') and isinstance(data.created_at, datetime):
                data.created_at = data.created_at.isoformat()
            if hasattr(data, 'updated_at') and isinstance(data.updated_at, datetime):
                data.updated_at = data.updated_at.isoformat()
        return data

    class Config:
        from_attributes = True

