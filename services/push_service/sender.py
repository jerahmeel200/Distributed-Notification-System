"""
Push Notification Sender - Supports FCM HTTP v1 API
"""
import os
import json
import requests
from typing import Optional, Dict
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.logger import get_logger
from shared.retry import retry_with_backoff

logger = get_logger(__name__)


class PushSender:
    def __init__(self):
        # FCM HTTP v1 API configuration
        self.fcm_project_id = os.getenv("FCM_PROJECT_ID")
        self.fcm_service_account_path = os.getenv("FCM_SERVICE_ACCOUNT_PATH")
        self.fcm_service_account_json = os.getenv("FCM_SERVICE_ACCOUNT_JSON")
        
        # Legacy support (deprecated)
        self.fcm_server_key = os.getenv("FCM_SERVER_KEY")
        
        # Initialize OAuth token if service account is provided
        self.access_token = None
        if self.fcm_service_account_path or self.fcm_service_account_json:
            self._initialize_oauth_token()

    def _initialize_oauth_token(self):
        """Initialize OAuth 2.0 access token for FCM HTTP v1 API"""
        try:
            from google.oauth2 import service_account
            import google.auth.transport.requests
            
            # Load service account credentials
            if self.fcm_service_account_path:
                # Resolve path - handle both absolute and relative paths
                if not os.path.isabs(self.fcm_service_account_path):
                    # If relative, try to resolve from current working directory
                    resolved_path = os.path.abspath(self.fcm_service_account_path)
                    if not os.path.exists(resolved_path):
                        # Try from /app (Docker working directory)
                        resolved_path = os.path.join('/app', os.path.basename(self.fcm_service_account_path))
                else:
                    resolved_path = self.fcm_service_account_path
                
                if not os.path.exists(resolved_path):
                    raise FileNotFoundError(
                        f"FCM service account file not found at: {resolved_path} "
                        f"(original path: {self.fcm_service_account_path}). "
                        f"Please ensure the file exists or use FCM_SERVICE_ACCOUNT_JSON instead."
                    )
                
                credentials = service_account.Credentials.from_service_account_file(
                    resolved_path,
                    scopes=['https://www.googleapis.com/auth/firebase.messaging']
                )
            elif self.fcm_service_account_json:
                service_account_info = json.loads(self.fcm_service_account_json)
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=['https://www.googleapis.com/auth/firebase.messaging']
                )
            else:
                return
            
            # Refresh token
            request = google.auth.transport.requests.Request()
            credentials.refresh(request)
            self.access_token = credentials.token
            logger.info("FCM OAuth token initialized successfully")
        except ImportError:
            logger.error("google-auth library not installed. Install with: pip install google-auth google-auth-oauthlib")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize FCM OAuth token: {e}")
            raise

    def _get_access_token(self) -> str:
        """Get or refresh OAuth access token"""
        if not self.access_token:
            self._initialize_oauth_token()
        return self.access_token

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def send(self, token: str, title: str, body: str, data: Optional[Dict] = None) -> bool:
        """Send push notification via FCM"""
        # Try FCM HTTP v1 API first (new method)
        if self.fcm_project_id and (self.fcm_service_account_path or self.fcm_service_account_json):
            return self._send_via_fcm_v1(token, title, body, data)
        # Fallback to legacy API (deprecated)
        elif self.fcm_server_key:
            logger.warning("Using deprecated FCM Legacy API. Please migrate to HTTP v1 API.")
            return self._send_via_fcm_legacy(token, title, body, data)
        else:
            logger.warning("No FCM configuration found, using mock sender")
            return self._send_mock(token, title, body, data)

    def _send_via_fcm_v1(self, token: str, title: str, body: str, data: Optional[Dict] = None) -> bool:
        """Send push notification via FCM HTTP v1 API (recommended)"""
        try:
            access_token = self._get_access_token()
            url = f"https://fcm.googleapis.com/v1/projects/{self.fcm_project_id}/messages:send"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # FCM HTTP v1 message format
            message = {
                "message": {
                    "token": token,
                    "notification": {
                        "title": title,
                        "body": body
                    }
                }
            }
            
            # Add data payload if provided
            if data:
                message["message"]["data"] = {str(k): str(v) for k, v in data.items()}
            
            response = requests.post(
                url,
                json=message,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Push notification sent via FCM HTTP v1 to {token[:20]}...")
            return True
        except Exception as e:
            logger.error(f"FCM HTTP v1 error: {e}")
            # Try to refresh token and retry once
            if "401" in str(e) or "403" in str(e):
                try:
                    self._initialize_oauth_token()
                    return self._send_via_fcm_v1(token, title, body, data)
                except:
                    pass
            raise

    def _send_via_fcm_legacy(self, token: str, title: str, body: str, data: Optional[Dict] = None) -> bool:
        """Send push notification via FCM Legacy API (deprecated)"""
        try:
            headers = {
                "Authorization": f"key={self.fcm_server_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "to": token,
                "notification": {
                    "title": title,
                    "body": body
                },
                "data": data or {}
            }
            response = requests.post(
                "https://fcm.googleapis.com/fcm/send",
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Push notification sent via FCM Legacy API to {token[:20]}...")
            return True
        except Exception as e:
            logger.error(f"FCM Legacy API error: {e}")
            raise

    def _send_mock(self, token: str, title: str, body: str, data: Optional[Dict] = None) -> bool:
        """Mock push sender for development"""
        logger.info(f"[MOCK] Push to {token[:20]}...: {title}")
        logger.debug(f"[MOCK] Body: {body[:100]}...")
        return True

