"""
Initialize sample templates in the database
"""
import requests
import json

TEMPLATE_SERVICE_URL = "http://localhost:8004"

templates = [
    {
        "code": "welcome_email",
        "name": "Welcome Email",
        "subject": "Welcome {{name}}!",
        "body": "<h1>Welcome {{name}}!</h1><p>Thank you for joining us. Click <a href='{{link}}'>here</a> to get started.</p>",
        "notification_type": "email",
        "language": "en"
    },
    {
        "code": "password_reset_email",
        "name": "Password Reset Email",
        "subject": "Reset your password",
        "body": "<h1>Password Reset</h1><p>Hello {{name}}, click <a href='{{link}}'>here</a> to reset your password.</p>",
        "notification_type": "email",
        "language": "en"
    },
    {
        "code": "welcome_push",
        "name": "Welcome Push Notification",
        "subject": "Welcome {{name}}!",
        "body": "Thank you for joining us! Tap to get started.",
        "notification_type": "push",
        "language": "en"
    },
    {
        "code": "order_confirmation_email",
        "name": "Order Confirmation",
        "subject": "Order Confirmed - {{name}}",
        "body": "<h1>Order Confirmed</h1><p>Hello {{name}}, your order has been confirmed. View details <a href='{{link}}'>here</a>.</p>",
        "notification_type": "email",
        "language": "en"
    },
    {
        "code": "order_shipped",
        "name": "Order Shipped Push Notification",
        "subject": "Your order has been shipped!",
        "body": "Hello {{name}}, your order has been shipped! Track it here: {{link}}",
        "notification_type": "push",
        "language": "en"
    }
]

def create_templates():
    """Create sample templates"""
    for template in templates:
        try:
            response = requests.post(
                f"{TEMPLATE_SERVICE_URL}/api/v1/templates/",
                json=template
            )
            if response.status_code == 201:
                print(f"✓ Created template: {template['code']}")
            else:
                print(f"✗ Failed to create {template['code']}: {response.text}")
        except Exception as e:
            print(f"✗ Error creating {template['code']}: {e}")

if __name__ == "__main__":
    print("Initializing templates...")
    create_templates()
    print("Done!")

