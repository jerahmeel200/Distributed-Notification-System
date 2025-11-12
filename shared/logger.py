"""
Centralized logging with correlation IDs
"""
import logging
import uuid
from contextvars import ContextVar
from typing import Optional

correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class CorrelationIDFilter(logging.Filter):
    """Add correlation ID to log records"""
    def filter(self, record):
        record.correlation_id = correlation_id.get() or 'no-id'
        return True


def get_logger(name: str) -> logging.Logger:
    """Get logger with correlation ID support"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '[correlation_id:%(correlation_id)s] - %(message)s'
        )
        handler.setFormatter(formatter)
        handler.addFilter(CorrelationIDFilter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger


def set_correlation_id(cid: Optional[str] = None) -> str:
    """Set correlation ID for current context"""
    if cid is None:
        cid = str(uuid.uuid4())
    correlation_id.set(cid)
    return cid

