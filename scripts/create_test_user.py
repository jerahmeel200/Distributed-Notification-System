"""
Create a test user for testing
"""
import requests
import json

USER_SERVICE_URL = "http://localhost:8001"

user_data = {
    "name": "Test User",
    "email": "test@example.com",
    "password": "testpass123",
    "push_token": "test_push_token_12345",
    "preferences": {
        "email": True,
        "push": True
    }
}

def create_user():
    """Create test user"""
    try:
        response = requests.post(
            f"{USER_SERVICE_URL}/api/v1/users/",
            json=user_data
        )
        if response.status_code == 201:
            data = response.json()
            print(f"✓ User created successfully!")
            print(f"  User ID: {data.get('data', {}).get('id')}")
            print(f"  Email: {data.get('data', {}).get('email')}")
            
            # Login to get token
            login_response = requests.post(
                f"{USER_SERVICE_URL}/api/v1/users/login",
                json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                }
            )
            if login_response.status_code == 200:
                token_data = login_response.json()
                token = token_data.get('data', {}).get('access_token')
                print(f"\n✓ Login successful!")
                print(f"  Access Token: {token}")
                print(f"\nUse this token for API Gateway requests:")
                print(f"  Authorization: Bearer {token}")
        else:
            print(f"✗ Failed to create user: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("Creating test user...")
    create_user()
    print("\nDone!")

