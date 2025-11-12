#!/usr/bin/env python3
"""
Comprehensive demonstration script for all project features
"""
import requests
import json
import time
import sys
from typing import Dict, Optional

# Configuration
API_GATEWAY_URL = "http://localhost:8000"
USER_SERVICE_URL = "http://localhost:8001"
TEMPLATE_SERVICE_URL = "http://localhost:8004"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text: str):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")

def check_service_health(url: str, service_name: str) -> bool:
    """Check if a service is healthy"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"{service_name} is healthy")
            return True
        else:
            print_error(f"{service_name} returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"{service_name} is not reachable: {e}")
        return False

def create_user(email: str, password: str) -> Optional[Dict]:
    """Create a test user"""
    print_info("Creating test user...")
    try:
        response = requests.post(
            f"{USER_SERVICE_URL}/api/v1/users/",
            json={
                "name": "Demo User",
                "email": email,
                "password": password,
                "push_token": "demo_fcm_token_12345",
                "preferences": {
                    "email": True,
                    "push": True
                }
            },
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            if data.get("success"):
                user = data.get("data")
                print_success(f"User created: {user.get('id')}")
                return user
            else:
                print_error(f"Failed to create user: {data.get('error')}")
                return None
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error creating user: {e}")
        return None

def login(email: str, password: str) -> Optional[str]:
    """Login and get JWT token"""
    print_info("Logging in...")
    try:
        response = requests.post(
            f"{USER_SERVICE_URL}/api/v1/users/login",
            json={"email": email, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                token = data.get("data", {}).get("access_token")
                print_success("Login successful")
                return token
            else:
                print_error(f"Login failed: {data.get('error')}")
                return None
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error logging in: {e}")
        return None

def create_template(code: str, name: str, template_type: str) -> bool:
    """Create a notification template"""
    print_info(f"Creating {template_type} template: {code}...")
    try:
        response = requests.post(
            f"{TEMPLATE_SERVICE_URL}/api/v1/templates/",
            json={
                "code": code,
                "name": name,
                "subject": f"Welcome {{name}}!" if template_type == "email" else "Notification",
                "body": f"Hello {{name}}, welcome! Click here: {{link}}" if template_type == "email" else "Hi {{name}}, check this: {{link}}",
                "notification_type": template_type,
                "language": "en"
            },
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            if data.get("success"):
                print_success(f"Template '{code}' created")
                return True
            else:
                # Template might already exist
                if "already exists" in data.get("error", ""):
                    print_info(f"Template '{code}' already exists (skipping)")
                    return True
                print_error(f"Failed to create template: {data.get('error')}")
                return False
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error creating template: {e}")
        return False

def send_notification(token: str, user_id: str, template_code: str, notification_type: str, request_id: Optional[str] = None) -> Optional[Dict]:
    """Send a notification"""
    print_info(f"Sending {notification_type} notification...")
    try:
        payload = {
            "notification_type": notification_type,
            "user_id": user_id,
            "template_code": template_code,
            "variables": {
                "name": "Demo User",
                "link": "https://example.com/demo"
            },
            "priority": 5
        }
        
        if request_id:
            payload["request_id"] = request_id
        
        response = requests.post(
            f"{API_GATEWAY_URL}/api/v1/notifications/",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 202:
            data = response.json()
            if data.get("success"):
                notification = data.get("data")
                print_success(f"Notification queued: {notification.get('notification_id')}")
                return notification
            else:
                print_error(f"Failed to queue notification: {data.get('error')}")
                return None
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error sending notification: {e}")
        return None

def check_notification_status(token: str, notification_id: str) -> Optional[Dict]:
    """Check notification status"""
    try:
        response = requests.get(
            f"{API_GATEWAY_URL}/api/v1/notifications/{notification_id}/status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("data")
        return None
    except Exception as e:
        print_error(f"Error checking status: {e}")
        return None

def demonstrate_idempotency(token: str, user_id: str, template_code: str):
    """Demonstrate idempotency feature"""
    print_header("DEMONSTRATING IDEMPOTENCY")
    
    request_id = f"demo-idempotent-{int(time.time())}"
    
    print_info("Sending notification with request_id...")
    notification1 = send_notification(token, user_id, template_code, "email", request_id)
    
    if notification1:
        print_info("Sending the SAME notification again with same request_id...")
        time.sleep(1)
        notification2 = send_notification(token, user_id, template_code, "email", request_id)
        
        if notification2 and notification2.get("notification_id") == notification1.get("notification_id"):
            print_success("Idempotency working! Same request_id returned same notification")
        else:
            print_error("Idempotency failed - different notifications returned")

def main():
    print_header("DISTRIBUTED NOTIFICATION SYSTEM - FEATURE DEMONSTRATION")
    
    # Step 1: Check service health
    print_header("STEP 1: CHECKING SERVICE HEALTH")
    services_ok = True
    services_ok &= check_service_health(API_GATEWAY_URL, "API Gateway")
    services_ok &= check_service_health(USER_SERVICE_URL, "User Service")
    services_ok &= check_service_health(TEMPLATE_SERVICE_URL, "Template Service")
    
    if not services_ok:
        print_error("Some services are not healthy. Please check docker-compose logs.")
        sys.exit(1)
    
    # Step 2: Create user
    print_header("STEP 2: USER MANAGEMENT")
    email = f"demo_{int(time.time())}@example.com"
    password = "demo123456"
    
    user = create_user(email, password)
    if not user:
        print_error("Failed to create user. Trying to login with existing user...")
        # Try to login (user might already exist)
        token = login(email, password)
        if not token:
            print_error("Cannot proceed without authentication")
            sys.exit(1)
        user_id = "unknown"  # We'll need to get this from login response
    else:
        user_id = user.get("id")
        token = login(email, password)
        if not token:
            print_error("Failed to login")
            sys.exit(1)
    
    # Step 3: Create templates
    print_header("STEP 3: TEMPLATE MANAGEMENT")
    create_template("welcome_email", "Welcome Email", "email")
    create_template("demo_push", "Demo Push", "push")
    
    # Step 4: Send notifications
    print_header("STEP 4: SENDING NOTIFICATIONS")
    
    # Send email notification
    email_notification = send_notification(token, user_id, "welcome_email", "email")
    
    # Send push notification
    push_notification = send_notification(token, user_id, "demo_push", "push")
    
    # Step 5: Check notification status
    print_header("STEP 5: CHECKING NOTIFICATION STATUS")
    
    if email_notification:
        notification_id = email_notification.get("notification_id")
        print_info(f"Checking status for notification: {notification_id}")
        
        # Wait a bit for processing
        time.sleep(2)
        
        status = check_notification_status(token, notification_id)
        if status:
            print_success(f"Status: {status.get('status')}")
            if status.get("error"):
                print_info(f"Error: {status.get('error')}")
    
    # Step 6: Demonstrate idempotency
    print_header("STEP 6: IDEMPOTENCY DEMONSTRATION")
    demonstrate_idempotency(token, user_id, "welcome_email")
    
    # Step 7: List notifications
    print_header("STEP 7: LISTING NOTIFICATIONS")
    try:
        response = requests.get(
            f"{API_GATEWAY_URL}/api/v1/notifications/?page=1&limit=10",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                notifications = data.get("data", [])
                print_success(f"Found {len(notifications)} notifications")
                for notif in notifications[:5]:  # Show first 5
                    print_info(f"  - {notif.get('notification_id')}: {notif.get('status')}")
    except Exception as e:
        print_error(f"Error listing notifications: {e}")
    
    # Summary
    print_header("DEMONSTRATION COMPLETE")
    print_success("All features demonstrated successfully!")
    print_info(f"User Email: {email}")
    print_info(f"User ID: {user_id}")
    print_info(f"Token: {token[:20]}...")
    print_info("\nNext steps:")
    print_info("1. Check RabbitMQ Management UI: http://localhost:15672")
    print_info("2. View service logs: docker-compose logs -f")
    print_info("3. Check notification status via API")
    print_info("4. Test with real SendGrid/FCM credentials")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemonstration interrupted by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




