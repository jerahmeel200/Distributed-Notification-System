"""
User Service Database Models
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, Any
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    push_token = Column(String, nullable=True)
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Pydantic models
class UserPreference(BaseModel):
    email: bool = True
    push: bool = True


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    push_token: Optional[str] = None
    preferences: UserPreference = UserPreference()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password length (bcrypt has 72 byte limit)"""
        if isinstance(v, str):
            password_bytes = v.encode('utf-8')
            if len(password_bytes) > 72:
                raise ValueError("Password cannot exceed 72 bytes (approximately 72 characters for ASCII)")
        return v
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    push_token: Optional[str] = None
    preferences: Optional[UserPreference] = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    push_token: Optional[str]
    email_enabled: bool
    push_enabled: bool
    created_at: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def convert_datetime_fields(cls, data: Any) -> Any:
        """Convert datetime objects to ISO format strings before validation"""
        if isinstance(data, dict):
            if 'created_at' in data and isinstance(data['created_at'], datetime):
                data['created_at'] = data['created_at'].isoformat()
        elif hasattr(data, '__dict__'):
            # Handle ORM objects
            if hasattr(data, 'created_at') and isinstance(data.created_at, datetime):
                data.created_at = data.created_at.isoformat()
        return data

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str

