"""
HTTP Client for inter-service communication
"""
import requests
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.logger import get_logger
from shared.circuit_breaker import circuit_breaker

logger = get_logger(__name__)


class HTTPClient:
    def __init__(self):
        self.template_service_url = os.getenv("TEMPLATE_SERVICE_URL", "http://localhost:8004")
        self.user_service_url = os.getenv("USER_SERVICE_URL", "http://localhost:8001")

    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    def get_user(self, user_id: str) -> dict:
        """Get user data from User Service (internal endpoint)"""
        try:
            service_token = os.getenv("SERVICE_TOKEN", "internal-service-token")
            response = requests.get(
                f"{self.user_service_url}/internal/users/{user_id}",
                headers={"X-Service-Token": service_token},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            if data.get("success") and data.get("data"):
                return data["data"]
            return None
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            raise

    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    def get_template(self, template_code: str) -> dict:
        """Get template from Template Service"""
        try:
            response = requests.get(
                f"{self.template_service_url}/api/v1/templates/{template_code}",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            if data.get("success") and data.get("data"):
                return data["data"]
            return None
        except Exception as e:
            logger.error(f"Error fetching template {template_code}: {e}")
            raise

