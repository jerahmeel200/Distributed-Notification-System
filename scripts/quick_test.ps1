# Quick Test Script for Notification System (PowerShell)
# This script tests the entire notification flow

$ErrorActionPreference = "Stop"

$BASE_URL = "http://localhost:8000"
$USER_SERVICE = "http://localhost:8001"

Write-Host "🚀 Starting Notification System Test" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if services are running
Write-Host "📡 Checking services..." -ForegroundColor Yellow
try {
    $healthCheck = Invoke-WebRequest -Uri "$BASE_URL/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Services are running" -ForegroundColor Green
} catch {
    Write-Host "❌ API Gateway is not running. Please start services with: docker-compose up -d" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 1: Login
Write-Host "🔐 Step 1: Logging in..." -ForegroundColor Yellow
$loginBody = @{
    email = "test@example.com"
    password = "testpass123"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$USER_SERVICE/api/v1/users/login" `
        -Method Post `
        -ContentType "application/json" `
        -Body $loginBody

    $TOKEN = $loginResponse.data.access_token
    $USER_ID = $loginResponse.data.id

    if (-not $TOKEN) {
        Write-Host "❌ Login failed. Please run: python scripts/create_test_user.py" -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ Login successful" -ForegroundColor Green
    Write-Host "   User ID: $USER_ID"
} catch {
    Write-Host "❌ Login failed: $_" -ForegroundColor Red
    Write-Host "   Please run: python scripts/create_test_user.py" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Step 2: Create Email Notification
Write-Host "📧 Step 2: Creating email notification..." -ForegroundColor Yellow
$requestId = "test-email-$(Get-Date -Format 'yyyyMMddHHmmss')"
$emailBody = @{
    notification_type = "email"
    user_id = $USER_ID
    template_code = "welcome_email"
    variables = @{
        name = "Test User"
        link = "https://example.com/welcome"
    }
    request_id = $requestId
    priority = 5
} | ConvertTo-Json -Depth 10

try {
    $headers = @{
        "Authorization" = "Bearer $TOKEN"
        "Content-Type" = "application/json"
    }

    $emailResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/notifications/" `
        -Method Post `
        -Headers $headers `
        -Body $emailBody

    $NOTIFICATION_ID = $emailResponse.data.notification_id

    Write-Host "✅ Email notification created" -ForegroundColor Green
    Write-Host "   Notification ID: $NOTIFICATION_ID"
} catch {
    Write-Host "❌ Failed to create notification: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Wait and Check Status
Write-Host "⏳ Step 3: Waiting for processing (5 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "📊 Checking notification status..." -ForegroundColor Yellow
try {
    $statusResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/notifications/$NOTIFICATION_ID/status" `
        -Method Get `
        -Headers @{"Authorization" = "Bearer $TOKEN"}

    $STATUS = $statusResponse.data.status
    Write-Host "✅ Status retrieved" -ForegroundColor Green
    Write-Host "   Status: $STATUS"
} catch {
    Write-Host "⚠️  Could not retrieve status: $_" -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Create Push Notification
Write-Host "📱 Step 4: Creating push notification..." -ForegroundColor Yellow
$pushRequestId = "test-push-$(Get-Date -Format 'yyyyMMddHHmmss')"
$pushBody = @{
    notification_type = "push"
    user_id = $USER_ID
    template_code = "welcome_push"
    variables = @{
        name = "Test User"
        link = "https://example.com/welcome"
    }
    request_id = $pushRequestId
    priority = 5
} | ConvertTo-Json -Depth 10

try {
    $pushResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/notifications/" `
        -Method Post `
        -Headers $headers `
        -Body $pushBody

    $PUSH_NOTIFICATION_ID = $pushResponse.data.notification_id
    Write-Host "✅ Push notification created" -ForegroundColor Green
    Write-Host "   Notification ID: $PUSH_NOTIFICATION_ID"
} catch {
    Write-Host "⚠️  Push notification may have failed (check if push_token is set): $_" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "✅ Test completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "   - Email notification: $NOTIFICATION_ID"
Write-Host "   - Push notification: $PUSH_NOTIFICATION_ID"
Write-Host ""
Write-Host "🔍 Next steps:" -ForegroundColor Cyan
Write-Host "   - Check RabbitMQ: http://localhost:15672"
Write-Host "   - View logs: docker-compose logs -f"
Write-Host "   - Check status: Invoke-RestMethod -Uri '$BASE_URL/api/v1/notifications/$NOTIFICATION_ID/status' -Headers @{'Authorization'='Bearer $TOKEN'}"
Write-Host ""








