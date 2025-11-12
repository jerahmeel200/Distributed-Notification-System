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
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment and testing guide

## Documentation

- **🚀 Quick Start**: See `QUICKSTART.md` - Get running in minutes!
- **Quick Setup**: See `SETUP.md` for basic setup instructions
- **FCM Migration**: See `docs/FCM_MIGRATION.md` - Migrate from Legacy to HTTP v1 API
- **Complete Guide**: See `DEPLOYMENT.md` for detailed instructions on:
  - Starting the project
  - Testing (manual and automated)
  - Deployment (Docker, Cloud, Kubernetes)
  - Troubleshooting
  - Production checklist

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

## CI/CD

GitHub Actions workflows are configured in `.github/workflows/`. The pipeline:
1. Runs tests
2. Builds Docker images
3. Deploys to server (when using `/request-server`)

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

