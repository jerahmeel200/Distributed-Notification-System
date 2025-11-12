"""
Email Service - Processes email notifications from queue
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import asyncio
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.models import NotificationStatus
from shared.logger import get_logger, set_correlation_id, correlation_id
from shared.retry import retry_with_backoff
from shared.circuit_breaker import CircuitBreaker
from consumer import EmailConsumer
from sender import EmailSender

logger = get_logger(__name__)

app = FastAPI(
    title="Email Service",
    description="Email notification processing service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request, call_next):
    """Add correlation ID to requests"""
    cid = request.headers.get("X-Correlation-ID")
    set_correlation_id(cid)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id.get() or 'no-id'
    return response


@app.on_event("startup")
async def startup_event():
    """Start email consumer on startup"""
    logger.info("Email Service started")
    consumer = EmailConsumer()
    asyncio.create_task(consumer.start_consuming())


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "email_service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

