# System Design - Distributed Notification System

## Architecture Overview

The notification system is built using a microservices architecture with asynchronous message queuing. The system consists of 5 independent services that communicate via REST APIs and message queues.

## System Components

### 1. API Gateway Service
- **Port**: 8000
- **Responsibilities**:
  - Entry point for all client requests
  - Request validation and authentication
  - Routes notifications to appropriate queues
  - Tracks notification status
  - Idempotency handling

### 2. User Service
- **Port**: 8001
- **Database**: PostgreSQL (user_db)
- **Responsibilities**:
  - User management (CRUD operations)
  - Authentication and authorization
  - User preferences management
  - Push token management

### 3. Template Service
- **Port**: 8004
- **Database**: PostgreSQL (template_db)
- **Responsibilities**:
  - Template storage and versioning
  - Template variable substitution
  - Multi-language support

### 4. Email Service
- **Port**: 8002
- **Responsibilities**:
  - Consumes messages from email.queue
  - Renders templates with user data
  - Sends emails via SendGrid or SMTP
  - Updates notification status

### 5. Push Service
- **Port**: 8003
- **Responsibilities**:
  - Consumes messages from push.queue
  - Renders templates with user data
  - Sends push notifications via FCM
  - Updates notification status

## Message Queue Architecture

### RabbitMQ Setup

```
Exchange: notifications.direct (direct type, durable)

Queues:
├── email.queue → Email Service
├── push.queue → Push Service
└── failed.queue → Dead Letter Queue
```

### Message Flow

1. Client sends notification request to API Gateway
2. API Gateway validates request and publishes to appropriate queue
3. Email/Push Service consumes message
4. Service fetches user data and template
5. Service renders template and sends notification
6. Service updates status via API Gateway

## Database Schema

### User Service (PostgreSQL)
```sql
users (
    id UUID PRIMARY KEY,
    name VARCHAR,
    email VARCHAR UNIQUE,
    password_hash VARCHAR,
    push_token VARCHAR,
    email_enabled BOOLEAN,
    push_enabled BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Template Service (PostgreSQL)
```sql
templates (
    id UUID PRIMARY KEY,
    code VARCHAR UNIQUE,
    name VARCHAR,
    subject VARCHAR,
    body TEXT,
    notification_type VARCHAR,
    language VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### API Gateway (PostgreSQL)
```sql
notifications (
    id UUID PRIMARY KEY,
    user_id VARCHAR,
    notification_type VARCHAR,
    template_code VARCHAR,
    status VARCHAR,
    priority INTEGER,
    metadata JSONB,
    error TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

## Failure Handling

### Circuit Breaker Pattern
- Prevents cascading failures when external services are down
- Threshold: 5 failures
- Recovery timeout: 60 seconds
- States: CLOSED → OPEN → HALF_OPEN

### Retry Mechanism
- Exponential backoff: 1s → 2s → 4s
- Max retries: 3 attempts
- Failed messages moved to dead-letter queue after max retries

### Dead Letter Queue
- Permanently failed messages stored in `failed.queue`
- Can be manually reviewed and reprocessed
- Logs include full error details

## Service Communication

### Synchronous (REST)
- User preference lookups
- Template retrieval
- Status queries
- Authentication

### Asynchronous (Message Queue)
- Notification processing
- Retry handling
- Status updates

## Scalability

### Horizontal Scaling
- All services are stateless and can be scaled independently
- Multiple instances can consume from same queues
- Load balancer distributes requests to API Gateway instances

### Performance Targets
- 1,000+ notifications per minute
- API Gateway response < 100ms
- 99.5% delivery success rate

## Monitoring & Logging

### Health Checks
- All services expose `/health` endpoint
- Docker health checks configured
- Service discovery ready

### Logging
- Correlation IDs for request tracking
- Structured logging with service name
- Error tracking with stack traces

### Metrics (Recommended)
- Message rate per queue
- Service response times
- Error rates
- Queue length and lag

## Security

### Authentication
- JWT tokens for API access
- Token expiration: 24 hours
- Password hashing with bcrypt

### Authorization
- Users can only access their own data
- Service-to-service communication uses internal network

## Deployment

### Docker Compose
- All services containerized
- Network isolation
- Volume persistence for databases

### CI/CD Pipeline
1. Run tests
2. Build Docker images
3. Deploy to server

## Technology Stack

- **Language**: Python 3.11
- **Framework**: FastAPI
- **Message Queue**: RabbitMQ
- **Databases**: PostgreSQL, Redis
- **Containerization**: Docker
- **API Documentation**: Swagger/OpenAPI

## Future Enhancements

1. Service mesh (Istio/Linkerd) for advanced traffic management
2. Distributed tracing (Jaeger/Zipkin)
3. Metrics collection (Prometheus + Grafana)
4. Rate limiting per user
5. Notification scheduling
6. Batch notifications
7. Webhook support for delivery confirmations

