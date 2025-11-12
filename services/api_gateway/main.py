"""
API Gateway - Entry point for all notification requests
"""
from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
import sys
import os
import pika
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.models import (
    ResponseModel, NotificationRequest, NotificationType,
    NotificationStatus, NotificationStatusUpdate, PaginationMeta
)
from shared.logger import get_logger, set_correlation_id, correlation_id
from shared.idempotency import IdempotencyManager
from database import get_db, init_db
from models import Notification, NotificationCreate
from auth import verify_token
from dependencies import get_current_user_id
from queue_manager import QueueManager
from http_client import HTTPClient
import redis

logger = get_logger(__name__)

app = FastAPI(
    title="Notification API Gateway",
    description="API Gateway for notification system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis for idempotency
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/4"))
idempotency_manager = IdempotencyManager(redis_client)
queue_manager = QueueManager()
http_client = HTTPClient()


@app.middleware("http")
async def correlation_id_middleware(request, call_next):
    """Add correlation ID to requests"""
    cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    set_correlation_id(cid)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id.get() or 'no-id'
    return response


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    init_db()
    queue_manager.initialize()
    logger.info("API Gateway started")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api_gateway"}


@app.post("/api/v1/notifications/", response_model=ResponseModel[dict], status_code=status.HTTP_202_ACCEPTED)
async def create_notification(
    notification: NotificationRequest,
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID"),
    user_id: str = Depends(get_current_user_id)
):
    """Create a notification request"""
    try:
        # Use request_id from body or generate one
        request_id = notification.request_id or str(uuid.uuid4())
        set_correlation_id(request_id)

        # Validate user can only create notifications for themselves
        if notification.user_id != user_id:
            return ResponseModel.error_response(
                error="Unauthorized: You can only create notifications for yourself",
                message="Notification creation failed"
            )

        # Check idempotency
        if idempotency_manager.is_duplicate(request_id, "notification"):
            cached = idempotency_manager.check_and_store(request_id, "notification", {})
            if cached:
                return ResponseModel.success_response(
                    data={"notification_id": request_id, "status": "pending"},
                    message="Notification already processed (idempotent)"
                )

        # Validate user exists
        user_data = http_client.get_user(notification.user_id)
        if not user_data:
            return ResponseModel.error_response(
                error="User not found",
                message="Notification creation failed"
            )

        # Validate template exists
        template = http_client.get_template(notification.template_code)
        if not template:
            return ResponseModel.error_response(
                error="Template not found",
                message="Notification creation failed"
            )

        # Check notification type matches template
        if template.get("notification_type") != notification.notification_type.value:
            return ResponseModel.error_response(
                error=f"Template type mismatch. Expected {notification.notification_type.value}",
                message="Notification creation failed"
            )

        # Create notification record
        db = next(get_db())
        db_notification = Notification(
            id=request_id,
            user_id=notification.user_id,
            notification_type=notification.notification_type.value,
            template_code=notification.template_code,
            status=NotificationStatus.pending.value,
            priority=notification.priority,
            notification_metadata=notification.metadata
        )
        db.add(db_notification)
        db.commit()
        db.close()

        # Publish to appropriate queue
        message = {
            "request_id": request_id,
            "user_id": notification.user_id,
            "template_code": notification.template_code,
            "variables": notification.variables.dict(),
            "priority": notification.priority,
            "metadata": notification.metadata
        }

        routing_key = notification.notification_type.value
        queue_manager.publish(routing_key, message)

        # Store idempotency result
        result = {"notification_id": request_id, "status": "pending"}
        idempotency_manager.check_and_store(request_id, "notification", result)

        logger.info(f"Notification created: {request_id}")
        return ResponseModel.success_response(
            data=result,
            message="Notification queued successfully"
        )

    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to create notification"
        )


@app.get("/api/v1/notifications/{notification_id}/status", response_model=ResponseModel[dict])
async def get_notification_status(
    notification_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get notification status"""
    try:
        db = next(get_db())
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            
            if not notification:
                return ResponseModel.error_response(
                    error="Notification not found",
                    message="Status retrieval failed"
                )

            # Users can only view their own notifications
            if str(notification.user_id) != user_id:
                return ResponseModel.error_response(
                    error="Unauthorized",
                    message="Access denied"
                )

            return ResponseModel.success_response(
                data={
                    "notification_id": notification.id,
                    "status": notification.status,
                    "created_at": notification.created_at.isoformat() if notification.created_at else None,
                    "updated_at": notification.updated_at.isoformat() if notification.updated_at else None,
                    "error": notification.error
                },
                message="Status retrieved successfully"
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error retrieving status: {e}")
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to retrieve status"
        )


@app.post("/api/v1/notifications/{notification_id}/status", response_model=ResponseModel[dict])
async def update_notification_status(
    notification_id: str,
    status_update: NotificationStatusUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """Update notification status (user endpoint)"""
    try:
        db = next(get_db())
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            
            if not notification:
                return ResponseModel.error_response(
                    error="Notification not found",
                    message="Status update failed"
                )

            # Users can only update their own notifications
            if str(notification.user_id) != user_id:
                return ResponseModel.error_response(
                    error="Unauthorized",
                    message="Access denied"
                )

            notification.status = status_update.status.value
            if status_update.error:
                notification.error = status_update.error
            notification.updated_at = datetime.now(timezone.utc)

            db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

        logger.info(f"Notification status updated: {notification_id} -> {status_update.status.value}")
        return ResponseModel.success_response(
            data={"notification_id": notification_id, "status": status_update.status.value},
            message="Status updated successfully"
        )
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to update status"
        )


@app.post("/internal/notifications/{notification_id}/status", response_model=ResponseModel[dict])
async def update_notification_status_internal(
    notification_id: str,
    status_update: NotificationStatusUpdate,
    x_service_token: Optional[str] = Header(None, alias="X-Service-Token")
):
    """Internal endpoint for updating notification status (called by email/push services)"""
    try:
        # Simple service token check
        service_token = os.getenv("SERVICE_TOKEN", "internal-service-token")
        if x_service_token != service_token:
            return ResponseModel.error_response(
                error="Unauthorized",
                message="Invalid service token"
            )

        db = next(get_db())
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            
            if not notification:
                return ResponseModel.error_response(
                    error="Notification not found",
                    message="Status update failed"
                )

            notification.status = status_update.status.value
            if status_update.error:
                notification.error = status_update.error
            notification.updated_at = datetime.now(timezone.utc)

            db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

        logger.info(f"Notification status updated: {notification_id} -> {status_update.status.value}")
        return ResponseModel.success_response(
            data={"notification_id": notification_id, "status": status_update.status.value},
            message="Status updated successfully"
        )
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to update status"
        )


@app.get("/api/v1/notifications/", response_model=ResponseModel[list])
async def list_notifications(
    page: int = 1,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id)
):
    """List user's notifications"""
    try:
        db = next(get_db())
        try:
            offset = (page - 1) * limit

            notifications = db.query(Notification).filter(
                Notification.user_id == user_id
            ).offset(offset).limit(limit).all()

            total = db.query(Notification).filter(Notification.user_id == user_id).count()
            total_pages = (total + limit - 1) // limit

            meta = PaginationMeta(
                total=total,
                limit=limit,
                page=page,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )

            data = [{
                "notification_id": n.id,
                "status": n.status,
                "notification_type": n.notification_type,
                "created_at": n.created_at.isoformat() if n.created_at else None
            } for n in notifications]

            return ResponseModel.success_response(
                data=data,
                message="Notifications retrieved successfully",
                meta=meta
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error listing notifications: {e}")
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to list notifications"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

