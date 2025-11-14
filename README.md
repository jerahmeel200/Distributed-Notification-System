# Distributed Notification System

A microservices-based notification system that sends emails and push notifications using asynchronous message queues.

## Architecture

The system consists of 5 microservices:

1. **API Gateway Service** - Entry point for all notification requests
2. **User Service** - Manages user data and preferences
3. **Email Service** - Handles email notifications via SMTP/SendGrid
4. **Push Service** - Handles push notifications via FCM
5. **Template Service** - Manages notification templates

## Tech Stack

- **Language**: Python 3.11+ with FastAPI
- **Message Queue**: RabbitMQ
- **Databases**: PostgreSQL (primary), Redis (caching)
- **Containerization**: Docker & Docker Compose
- **API Documentation**: Swagger/OpenAPI

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Free tier accounts for:
  - SendGrid (email) or Gmail SMTP
  - Firebase Cloud Messaging (FCM) for push notifications

## Quick Start

**🚀 New to the project?** See **[QUICKSTART.md](QUICKSTART.md)** for a step-by-step guide to get running in minutes!

### TL;DR

```bash
# 1. Create .env file with your credentials
# 2. Start services
docker-compose up -d

# 3. Initialize data
python scripts/create_test_user.py
python scripts/init_templates.py

# 4. Access API Gateway
# http://localhost:8000/docs
```

For detailed instructions, see:
- **[QUICKSTART.md](QUICKSTART.md)** - Complete quick start guide
- **[SETUP.md](SETUP.md)** - Detailed setup instructions
- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Deployment overview and recommendations

## Documentation

- **🚀 Quick Start**: See `QUICKSTART.md` - Get running in minutes!
- **Quick Setup**: See `SETUP.md` for basic setup instructions
- **🚀 Deployment**: 
  - **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Overview and quick recommendations
  - **[DEPLOYMENT_QUICK_START.md](DEPLOYMENT_QUICK_START.md)** - Fastest deployment options (10-30 min)
  - **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Comprehensive guide with 7 deployment options:
    - **⭐ Render.com (Recommended)** - Quick deployments with managed infrastructure
    - Docker Compose (Single Server)
    - Railway
    - AWS (ECS/Fargate)
    - Google Cloud Platform
    - Kubernetes (Production)
    - DigitalOcean App Platform
- **FCM Migration**: See `docs/FCM_MIGRATION.md` - Migrate from Legacy to HTTP v1 API

## API Endpoints

### API Gateway

- `POST /api/v1/notifications/` - Create notification
- `GET /api/v1/notifications/{notification_id}/status` - Get notification status

### User Service

- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/{user_id}` - Get user
- `PUT /api/v1/users/{user_id}` - Update user
- `POST /api/v1/users/login` - Login

### Template Service

- `POST /api/v1/templates/` - Create template
- `GET /api/v1/templates/{template_code}` - Get template
- `PUT /api/v1/templates/{template_code}` - Update template

## Development

### Running Services Locally

Each service can be run independently:

```bash
cd services/api_gateway
uvicorn main:app --reload --port 8000
```

### Running Tests

```bash
pytest
```

## Deployment

**🚀 Recommended: Deploy to Render.com**

The easiest way to deploy is using Render's Blueprint feature with the provided `render.yaml`:

1. Sign up at [render.com](https://render.com)
2. Connect your GitHub repository
3. Create a new Blueprint and select `render.yaml`
4. Configure environment variables (see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md))
5. Deploy!

See **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for complete instructions.

## CI/CD

GitHub Actions workflows are configured in `.github/workflows/`. The pipeline:
1. Runs tests
2. Builds Docker images
3. Deploys to server (when using `/request-server`)

Render also supports automatic deployments from Git - just connect your repository!

## System Design

See `docs/system_design.md` for detailed architecture diagrams and design decisions.

See `docs/architecture_diagram.txt` for diagram description to create visual architecture diagrams using Draw.io, Miro, or Lucidchart.

## Performance Targets

- Handle 1,000+ notifications per minute
- API Gateway response < 100ms
- 99.5% delivery success rate
- Horizontal scaling support

## Features

- ✅ Circuit Breaker pattern
- ✅ Retry with exponential backoff
- ✅ Dead Letter Queue
- ✅ Health checks
- ✅ Idempotency
- ✅ Service discovery
- ✅ Rate limiting
- ✅ Correlation IDs for logging

## License

MIT

