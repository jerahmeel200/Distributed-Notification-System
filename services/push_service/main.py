"""
Push Service - Processes push notifications from queue
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.logger import get_logger, set_correlation_id, correlation_id
from consumer import PushConsumer

logger = get_logger(__name__)

app = FastAPI(
    title="Push Service",
    description="Push notification processing service",
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
    """Start push consumer on startup"""
    logger.info("Push Service started")
    consumer = PushConsumer()
    asyncio.create_task(consumer.start_consuming())


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "push_service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

