"""
Shared data models and response formats
"""
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

T = TypeVar('T')


class NotificationType(str, Enum):
    email = "email"
    push = "push"


class NotificationStatus(str, Enum):
    delivered = "delivered"
    pending = "pending"
    failed = "failed"


class PaginationMeta(BaseModel):
    total: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ResponseModel(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    message: str
    meta: Optional[PaginationMeta] = None

    @classmethod
    def success_response(
        cls,
        data: T = None,
        message: str = "Success",
        meta: Optional[PaginationMeta] = None
    ):
        return cls(
            success=True,
            data=data,
            message=message,
            meta=meta
        )

    @classmethod
    def error_response(
        cls,
        error: str,
        message: str = "Error occurred"
    ):
        return cls(
            success=False,
            error=error,
            message=message
        )


class UserData(BaseModel):
    name: str
    link: str
    meta: Optional[dict] = None


class UserPreference(BaseModel):
    email: bool = True
    push: bool = True


class NotificationRequest(BaseModel):
    notification_type: NotificationType
    user_id: str
    template_code: str
    variables: UserData
    request_id: Optional[str] = None
    priority: int = 5
    metadata: Optional[dict] = None


class NotificationStatusUpdate(BaseModel):
    status: NotificationStatus
    timestamp: Optional[datetime] = None
    error: Optional[str] = None

