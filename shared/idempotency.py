"""
Idempotency handling using Redis
"""
import json
import hashlib
import logging
from typing import Optional, Any
import redis
from datetime import timedelta

logger = logging.getLogger(__name__)


class IdempotencyManager:
    def __init__(self, redis_client: redis.Redis, ttl: int = 3600):
        self.redis = redis_client
        self.ttl = ttl

    def generate_key(self, request_id: str, service: str) -> str:
        """Generate a unique key for idempotency check"""
        return f"idempotency:{service}:{request_id}"

    def check_and_store(
        self,
        request_id: str,
        service: str,
        result: Any
    ) -> Optional[Any]:
        """
        Check if request was already processed and return cached result
        If not, store the result for future requests
        """
        key = self.generate_key(request_id, service)
        
        # Check if already processed
        cached = self.redis.get(key)
        if cached:
            logger.info(f"Idempotent request detected: {request_id}")
            return json.loads(cached)

        # Store result
        result_json = json.dumps(result, default=str)
        self.redis.setex(key, self.ttl, result_json)
        return None

    def is_duplicate(self, request_id: str, service: str) -> bool:
        """Check if request is a duplicate"""
        key = self.generate_key(request_id, service)
        return self.redis.exists(key) > 0

