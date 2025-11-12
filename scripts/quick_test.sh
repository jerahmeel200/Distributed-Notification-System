#!/bin/bash

# Quick Test Script for Notification System
# This script tests the entire notification flow

set -e

BASE_URL="http://localhost:8000"
USER_SERVICE="http://localhost:8001"
TEMPLATE_SERVICE="http://localhost:8004"

echo "🚀 Starting Notification System Test"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if services are running
echo "📡 Checking services..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}❌ API Gateway is not running. Please start services with: docker-compose up -d${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Services are running${NC}"
echo ""

# Step 1: Login
echo "🔐 Step 1: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$USER_SERVICE/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
USER_ID=$(echo $LOGIN_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Login failed. Please run: python scripts/create_test_user.py${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Login successful${NC}"
echo "   User ID: $USER_ID"
echo ""

# Step 2: Create Email Notification
echo "📧 Step 2: Creating email notification..."
REQUEST_ID="test-email-$(date +%s)"
EMAIL_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/notifications/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"notification_type\": \"email\",
    \"user_id\": \"$USER_ID\",
    \"template_code\": \"welcome_email\",
    \"variables\": {
      \"name\": \"Test User\",
      \"link\": \"https://example.com/welcome\"
    },
    \"request_id\": \"$REQUEST_ID\",
    \"priority\": 5
  }")

NOTIFICATION_ID=$(echo $EMAIL_RESPONSE | grep -o '"notification_id":"[^"]*' | cut -d'"' -f4)

if [ -z "$NOTIFICATION_ID" ]; then
    echo -e "${RED}❌ Failed to create notification${NC}"
    echo "Response: $EMAIL_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ Email notification created${NC}"
echo "   Notification ID: $NOTIFICATION_ID"
echo ""

# Step 3: Wait and Check Status
echo "⏳ Step 3: Waiting for processing (5 seconds)..."
sleep 5

echo "📊 Checking notification status..."
STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/notifications/$NOTIFICATION_ID/status" \
  -H "Authorization: Bearer $TOKEN")

STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*' | cut -d'"' -f4)

if [ -z "$STATUS" ]; then
    echo -e "${YELLOW}⚠️  Could not retrieve status${NC}"
else
    echo -e "${GREEN}✅ Status retrieved${NC}"
    echo "   Status: $STATUS"
fi
echo ""

# Step 4: Create Push Notification
echo "📱 Step 4: Creating push notification..."
PUSH_REQUEST_ID="test-push-$(date +%s)"
PUSH_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/notifications/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"notification_type\": \"push\",
    \"user_id\": \"$USER_ID\",
    \"template_code\": \"welcome_push\",
    \"variables\": {
      \"name\": \"Test User\",
      \"link\": \"https://example.com/welcome\"
    },
    \"request_id\": \"$PUSH_REQUEST_ID\",
    \"priority\": 5
  }")

PUSH_NOTIFICATION_ID=$(echo $PUSH_RESPONSE | grep -o '"notification_id":"[^"]*' | cut -d'"' -f4)

if [ -z "$PUSH_NOTIFICATION_ID" ]; then
    echo -e "${YELLOW}⚠️  Push notification may have failed (check if push_token is set)${NC}"
else
    echo -e "${GREEN}✅ Push notification created${NC}"
    echo "   Notification ID: $PUSH_NOTIFICATION_ID"
fi
echo ""

# Summary
echo "======================================"
echo -e "${GREEN}✅ Test completed successfully!${NC}"
echo ""
echo "📋 Summary:"
echo "   - Email notification: $NOTIFICATION_ID"
echo "   - Push notification: $PUSH_NOTIFICATION_ID"
echo ""
echo "🔍 Next steps:"
echo "   - Check RabbitMQ: http://localhost:15672"
echo "   - View logs: docker-compose logs -f"
echo "   - Check status: curl -H \"Authorization: Bearer $TOKEN\" $BASE_URL/api/v1/notifications/$NOTIFICATION_ID/status"
echo ""








