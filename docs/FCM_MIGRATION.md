# FCM Migration Guide: Legacy API to HTTP v1 API

## Overview

Firebase Cloud Messaging (FCM) Legacy API was deprecated on June 20, 2023, and will stop working after June 20, 2024. This guide helps you migrate to the new FCM HTTP v1 API.

## What Changed?

### Legacy API (Deprecated)
- Uses Server Key for authentication
- Endpoint: `https://fcm.googleapis.com/fcm/send`
- Simple but less secure

### HTTP v1 API (Current)
- Uses OAuth 2.0 with Service Account
- Endpoint: `https://fcm.googleapis.com/v1/projects/{project_id}/messages:send`
- More secure and feature-rich

## Migration Steps

### Step 1: Get Service Account Credentials

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. Click the **gear icon** → **Project Settings**
4. Go to **Service Accounts** tab
5. Click **Generate New Private Key**
6. Save the JSON file (e.g., `fcm-service-account.json`)

### Step 2: Update Environment Variables

**Old Configuration (Legacy):**
```env
FCM_SERVER_KEY=your-server-key-here
```

**New Configuration (HTTP v1):**
```env
FCM_PROJECT_ID=your-firebase-project-id
FCM_SERVICE_ACCOUNT_PATH=./fcm-service-account.json
```

Or use JSON string directly:
```env
FCM_PROJECT_ID=your-firebase-project-id
FCM_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
```

### Step 3: Update Docker Configuration

If using Docker, mount the service account file:

```yaml
volumes:
  - ./fcm-service-account.json:/app/fcm-service-account.json:ro
```

Or pass the JSON as an environment variable.

### Step 4: Verify Migration

1. Restart the push service
2. Check logs for: `FCM OAuth token initialized successfully`
3. Send a test notification
4. Verify it works without legacy API warnings

## Code Changes

The push service has been updated to support both APIs:

- **HTTP v1 API** (preferred): Uses OAuth 2.0 authentication
- **Legacy API** (fallback): Still works but shows deprecation warnings

The service automatically uses HTTP v1 if service account credentials are provided.

## Troubleshooting

### Error: "google-auth library not installed"

**Solution:**
```bash
pip install google-auth google-auth-oauthlib
```

Or rebuild Docker containers:
```bash
docker-compose build push_service
docker-compose up -d push_service
```

### Error: "Invalid service account credentials"

**Solution:**
- Verify the JSON file is valid
- Check that the file path is correct
- Ensure the service account has "Firebase Cloud Messaging API" enabled

### Error: "Permission denied"

**Solution:**
- Ensure the service account has the "Firebase Cloud Messaging API" scope
- Check IAM permissions in Google Cloud Console

### Token Refresh Issues

The service automatically refreshes OAuth tokens. If you see 401/403 errors:
- Check service account credentials are valid
- Verify project ID is correct
- Ensure Firebase Cloud Messaging API is enabled

## Benefits of HTTP v1 API

1. **Better Security**: OAuth 2.0 instead of static keys
2. **More Features**: Better error handling, topic messaging, etc.
3. **Future-Proof**: Legacy API will stop working in 2024
4. **Better Performance**: More efficient message format

## Timeline

- **June 20, 2023**: Legacy API deprecated
- **June 20, 2024**: Legacy API stops working
- **Now**: Migrate to HTTP v1 API

## Need Help?

- [FCM HTTP v1 Documentation](https://firebase.google.com/docs/cloud-messaging/migrate-v1)
- [Service Account Setup](https://cloud.google.com/iam/docs/service-accounts)
- Check service logs: `docker-compose logs push_service`








