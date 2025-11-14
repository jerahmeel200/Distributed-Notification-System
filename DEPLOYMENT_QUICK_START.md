# Quick Deployment Reference

## 🚀 Fastest Deployment Options

### 1. Render.com (Recommended for Quick Start)

**Time: ~30 minutes**

1. Sign up at [render.com](https://render.com)
2. Connect GitHub repository
3. Create databases (PostgreSQL x2, Redis)
4. Deploy 5 web services (one per microservice)
5. Configure environment variables
6. Done!

**See full guide:** `DEPLOYMENT_GUIDE.md` → Option 2

---

### 2. Railway (Easiest CLI)

**Time: ~20 minutes**

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Add databases
railway add postgresql --name user-db
railway add postgresql --name template-db
railway add redis

# Deploy services
cd services/api_gateway && railway up
cd ../user_service && railway up
# ... repeat for all services
```

**See full guide:** `DEPLOYMENT_GUIDE.md` → Option 3

---

### 3. Docker Compose (Single Server)

**Time: ~10 minutes**

```bash
# On your VPS/server
git clone <your-repo>
cd Distributed-Notification-System

# Create .env file
nano .env  # Add your credentials

# Start everything
docker-compose up -d

# Initialize data
docker-compose exec api_gateway python scripts/create_test_user.py
docker-compose exec api_gateway python scripts/init_templates.py
```

**See full guide:** `DEPLOYMENT_GUIDE.md` → Option 1

---

## 📋 Pre-Deployment Checklist

- [ ] SendGrid API key (or SMTP credentials)
- [ ] Firebase FCM service account JSON file
- [ ] Strong JWT secret (generate random string)
- [ ] Domain name (optional)
- [ ] Environment variables documented

---

## 🔧 Environment Variables Template

Create a `.env` file with:

```bash
# Security
JWT_SECRET=your-strong-random-secret-here-min-32-chars
SERVICE_TOKEN=internal-service-token

# Databases (will be auto-configured on most platforms)
DATABASE_URL=postgresql://user:pass@host:5432/user_db
POSTGRES_USER_PASSWORD=strong-password-1
POSTGRES_TEMPLATE_PASSWORD=strong-password-2

# Message Queue
RABBITMQ_URL=amqp://guest:password@host:5672/
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=strong-password

# Cache
REDIS_URL=redis://host:6379/0

# Email Service
SENDGRID_API_KEY=SG.xxxxx
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-key
EMAIL_FROM=noreply@yourdomain.com

# Push Service
FCM_PROJECT_ID=your-fcm-project-id
```

---

## ✅ Post-Deployment Verification

```bash
# 1. Check API Gateway health
curl https://your-api-gateway-url/health

# 2. Check all services
curl https://your-user-service-url/health
curl https://your-template-service-url/health
curl https://your-email-service-url/health
curl https://your-push-service-url/health

# 3. Test authentication
curl -X POST https://your-api-gateway-url/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# 4. Create a test notification
curl -X POST https://your-api-gateway-url/api/v1/notifications/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-id",
    "template_code": "welcome_email",
    "notification_type": "email",
    "variables": {}
  }'
```

---

## 🆘 Common Issues

### Services can't connect to RabbitMQ
- Check RABBITMQ_URL format: `amqp://user:pass@host:5672/`
- Verify network connectivity between services
- Check RabbitMQ is running and accessible

### Database connection errors
- Verify DATABASE_URL format
- Check database is accessible from service network
- Ensure credentials are correct

### FCM push notifications not working
- Verify FCM service account JSON is mounted correctly
- Check FCM_PROJECT_ID matches JSON file
- Ensure JSON file path is correct: `/app/notification-service-d10e6-c3b98cba24f9.json`

### Email not sending
- Verify SENDGRID_API_KEY is set
- Check SMTP credentials if using SMTP
- Verify EMAIL_FROM domain is verified in SendGrid

---

## 📊 Platform Comparison

| Feature | Render | Railway | Docker Compose | AWS | GCP |
|---------|--------|---------|----------------|-----|-----|
| Setup Time | 30 min | 20 min | 10 min | 2+ hours | 1+ hour |
| Cost (Small) | $0-25 | $20-40 | $5-20 | $50-100 | $30-60 |
| Scalability | Medium | Medium | Low | High | High |
| Complexity | Low | Low | Low | High | Medium |
| Best For | Quick deploy | CLI lovers | VPS owners | Production | Serverless |

---

## 🎯 Recommendation by Use Case

- **Learning/Testing:** Docker Compose
- **Side Project:** Render.com (free tier)
- **Startup MVP:** Railway or Render
- **Production (Small):** Render or DigitalOcean
- **Production (Medium):** AWS ECS or GCP Cloud Run
- **Production (Large):** Kubernetes on AWS/GCP/Azure

---

For detailed instructions, see `DEPLOYMENT_GUIDE.md`

