# Deployment Guide - Distributed Notification System

This guide provides comprehensive deployment options for the Distributed Notification System.

## Table of Contents

1. [Deployment Options Overview](#deployment-options-overview)
2. [Prerequisites](#prerequisites)
3. [Option 1: Render.com ⭐ (Recommended)](#option-1-rendercom--recommended)
4. [Option 2: Docker Compose (Single Server)](#option-2-docker-compose-single-server)
5. [Option 3: Railway](#option-3-railway)
6. [Option 4: AWS (ECS/Fargate)](#option-4-aws-ecsfargate)
7. [Option 5: Google Cloud Platform](#option-5-google-cloud-platform)
8. [Option 6: Kubernetes (Production)](#option-6-kubernetes-production)
9. [Option 7: DigitalOcean App Platform](#option-7-digitalocean-app-platform)
10. [Environment Variables](#environment-variables)
11. [Post-Deployment Checklist](#post-deployment-checklist)

---

## Deployment Options Overview

| Platform | Complexity | Cost | Best For |
|----------|-----------|------|----------|
| **Render.com** ⭐ | **Low** | **Low-Medium** | **Recommended: Quick Deployments, Small to Medium Projects** |
| Docker Compose | Low | Low | Development, Single Server |
| Railway | Low | Medium | Quick Deployments |
| AWS ECS/Fargate | Medium | Medium-High | Production, Scalability |
| GCP Cloud Run | Low-Medium | Medium | Serverless, Auto-scaling |
| Kubernetes | High | High | Enterprise, High Scale |
| DigitalOcean | Low-Medium | Medium | Simple Production |

---

## Prerequisites

Before deploying, ensure you have:

1. **Service Accounts & API Keys:**
   - SendGrid API key (for email) OR SMTP credentials
   - Firebase Cloud Messaging (FCM) service account JSON
   - JWT secret key (generate a strong random string)

2. **Database & Infrastructure:**
   - PostgreSQL instances (2 databases: user_db, template_db)
   - Redis instance
   - RabbitMQ instance

3. **Domain & SSL:**
   - Domain name (optional but recommended)
   - SSL certificate (most platforms provide this)

---

## Option 1: Render.com ⭐ (Recommended)

**Best for:** Quick deployments with managed infrastructure. This is the recommended deployment option for most users.

### Quick Start (Using render.yaml)

The easiest way to deploy is using the provided `render.yaml` file:

1. **Sign up at [render.com](https://render.com)** and connect your GitHub repository

2. **Create a new Blueprint** (Infrastructure as Code):
   - In Render dashboard, click "New +" → "Blueprint"
   - Connect your repository
   - Render will automatically detect `render.yaml`
   - Review the services and click "Apply"

3. **Configure Environment Variables:**

   After the services are created, you need to set the following environment variables manually in the Render dashboard for each service:

   **For RabbitMQ service:**
   - `RABBITMQ_DEFAULT_PASS`: Set a strong password

   **For API Gateway:**
   - `JWT_SECRET`: Generate a strong random secret (e.g., `openssl rand -base64 32`)
   - `SERVICE_TOKEN`: Generate a random token for inter-service authentication
   - `RABBITMQ_URL`: Format: `amqp://guest:<RABBITMQ_DEFAULT_PASS>@<rabbitmq-service-hostname>:5672/`
     - Example: `amqp://guest:mypassword@rabbitmq.onrender.com:5672/`

   **For User Service:**
   - `JWT_SECRET`: Same value as API Gateway
   - `RABBITMQ_URL`: Same format as above

   **For Email Service:**
   - `SENDGRID_API_KEY`: Your SendGrid API key
   - `SMTP_PASSWORD`: Your SendGrid API key (same as SENDGRID_API_KEY)
   - `EMAIL_FROM`: Your sender email (e.g., `noreply@yourdomain.com`)
   - `RABBITMQ_URL`: Same format as above

   **For Push Service:**
   - `FCM_PROJECT_ID`: Your Firebase project ID
   - Upload the FCM service account JSON file as a Secret File in Render
   - `RABBITMQ_URL`: Same format as above

4. **Wait for all services to deploy** (this may take 10-15 minutes)

5. **Initialize data** (after services are running):
   ```bash
   # You can use Render's shell or run these via API
   # Create test user
   curl -X POST https://<api-gateway-url>/api/users/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"testpass123"}'
   
   # Initialize templates (if you have an init endpoint)
   ```

### Manual Setup (Alternative)

If you prefer to set up services manually:

1. **Create Infrastructure Services:**

   **PostgreSQL (User DB):**
   - New → PostgreSQL
   - Name: `user-db`
   - Database: `user_db`
   - User: `user_service`
   - Plan: Free (or Starter for production)

   **PostgreSQL (Template DB):**
   - New → PostgreSQL
   - Name: `template-db`
   - Database: `template_db`
   - User: `template_service`
   - Plan: Free (or Starter for production)

   **Redis:**
   - New → Redis
   - Name: `redis`
   - Plan: Free (or Starter for production)

   **RabbitMQ:**
   - New → Web Service
   - Name: `rabbitmq`
   - Environment: Docker
   - Dockerfile Path: `Dockerfile.rabbitmq`
   - Docker Context: `.`
   - Plan: Free (or Starter for production)
   - Environment Variables:
     - `RABBITMQ_DEFAULT_USER`: `guest`
     - `RABBITMQ_DEFAULT_PASS`: Set a strong password

2. **Deploy Application Services:**

   For each service (api-gateway, user-service, template-service, email-service, push-service):

   - New → Web Service
   - Connect your repository
   - Name: `{service-name}` (e.g., `api-gateway`)
   - Environment: `Docker`
   - Dockerfile Path: `services/{service_name}/Dockerfile`
   - Docker Context: `.`
   - Build Command: (auto-detected)
   - Start Command: (auto-detected)
   - Plan: Free (or Starter for production)

3. **Configure Service URLs:**

   After all services are deployed, update the service URLs in environment variables:
   - `USER_SERVICE_URL`: `https://user-service.onrender.com`
   - `TEMPLATE_SERVICE_URL`: `https://template-service.onrender.com`

### Important Notes:

- **Free Tier Limitations:** Services on the free tier will spin down after 15 minutes of inactivity. For production, upgrade to a paid plan.
- **RabbitMQ URL:** You'll need to construct the RabbitMQ URL manually using the RabbitMQ service hostname. Format: `amqp://guest:<password>@<rabbitmq-hostname>:5672/`
- **FCM Service Account:** Upload the JSON file as a Secret File in the Push Service settings.
- **Database Connections:** Render automatically provides connection strings via the `fromDatabase` references in `render.yaml`.

### Pros:
- ✅ Managed databases (PostgreSQL, Redis)
- ✅ Free tier available for testing
- ✅ Automatic SSL certificates
- ✅ Easy scaling with paid plans
- ✅ Infrastructure as Code with `render.yaml`
- ✅ Automatic deployments from Git

### Cons:
- ❌ Free tier services spin down after inactivity
- ❌ RabbitMQ needs manual setup (not a managed service)
- ❌ Free tier has resource limitations
- ❌ Some environment variables need manual configuration

---

## Option 2: Docker Compose (Single Server)

**Best for:** Development, testing, or small production deployments on a VPS.

### Steps:

1. **Prepare your server:**
   ```bash
   # Install Docker and Docker Compose
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   sudo apt-get install docker-compose-plugin
   ```

2. **Clone and configure:**
   ```bash
   git clone <your-repo>
   cd Distributed-Notification-System
   
   # Create .env file
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Deploy:**
   ```bash
   docker-compose up -d
   ```

4. **Initialize data:**
   ```bash
   docker-compose exec api_gateway python scripts/create_test_user.py
   docker-compose exec api_gateway python scripts/init_templates.py
   ```

5. **Access services:**
   - API Gateway: `http://your-server-ip:8000`
   - RabbitMQ Management: `http://your-server-ip:15672` (guest/guest)

### Pros:
- ✅ Simple setup
- ✅ All services in one place
- ✅ Easy to manage locally

### Cons:
- ❌ Single point of failure
- ❌ Limited scalability
- ❌ Manual updates required

---

## Option 3: Railway

**Best for:** Quick deployments with good developer experience.

### Steps:

1. **Install Railway CLI:**
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Create a new project:**
   ```bash
   railway init
   ```

3. **Add PostgreSQL services:**
   ```bash
   railway add postgresql --name user-db
   railway add postgresql --name template-db
   ```

4. **Add Redis:**
   ```bash
   railway add redis
   ```

5. **Add RabbitMQ:**
   - Use Railway's RabbitMQ plugin or deploy as a service

6. **Deploy each service:**
   ```bash
   # For each service directory
   cd services/api_gateway
   railway up
   ```

   Or use the provided script:
   ```bash
   ./scripts/railway_deploy.sh
   ```

7. **Set environment variables:**
   ```bash
   railway variables set DATABASE_URL=$DATABASE_URL
   railway variables set RABBITMQ_URL=$RABBITMQ_URL
   # ... etc
   ```

### Pros:
- ✅ Excellent CLI
- ✅ Simple pricing
- ✅ Good for startups

### Cons:
- ❌ Can get expensive at scale
- ❌ Less control than AWS/GCP

---

## Option 4: AWS (ECS/Fargate)

**Best for:** Production deployments requiring scalability and reliability.

### Architecture:

- **ECS Fargate** for containers (no server management)
- **RDS PostgreSQL** (Multi-AZ for production)
- **ElastiCache Redis**
- **Amazon MQ** (managed RabbitMQ) or **SQS** (alternative)
- **Application Load Balancer** for API Gateway
- **CloudWatch** for monitoring

### Steps:

1. **Create ECR repositories** for each service:
   ```bash
   aws ecr create-repository --repository-name notification-api-gateway
   aws ecr create-repository --repository-name notification-user-service
   # ... repeat for all services
   ```

2. **Build and push Docker images:**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Build and push
   docker build -f services/api_gateway/Dockerfile -t notification-api-gateway .
   docker tag notification-api-gateway:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/notification-api-gateway:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/notification-api-gateway:latest
   ```

3. **Create ECS Task Definitions** (one per service)

4. **Create ECS Cluster and Services**

5. **Set up RDS:**
   - Create 2 PostgreSQL instances (user_db, template_db)
   - Enable Multi-AZ for production

6. **Set up ElastiCache Redis**

7. **Set up Amazon MQ** (RabbitMQ) or use SQS

8. **Configure Application Load Balancer**

9. **Set up Secrets Manager** for sensitive data:
   ```bash
   aws secretsmanager create-secret --name notification/jwt-secret --secret-string "your-secret"
   aws secretsmanager create-secret --name notification/sendgrid-key --secret-string "your-key"
   ```

### Pros:
- ✅ Highly scalable
- ✅ Enterprise-grade reliability
- ✅ Comprehensive monitoring
- ✅ Managed services

### Cons:
- ❌ Complex setup
- ❌ Higher cost
- ❌ Steeper learning curve

---

## Option 5: Google Cloud Platform

**Best for:** Serverless deployments with auto-scaling.

### Architecture:

- **Cloud Run** for services (serverless containers)
- **Cloud SQL PostgreSQL** (2 instances)
- **Memorystore Redis**
- **Cloud Pub/Sub** (alternative to RabbitMQ) or **Cloud Tasks**
- **Cloud Load Balancing**

### Steps:

1. **Enable APIs:**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable sqladmin.googleapis.com
   gcloud services enable redis.googleapis.com
   ```

2. **Create Cloud SQL instances:**
   ```bash
   gcloud sql instances create user-db --database-version=POSTGRES_15 --tier=db-f1-micro
   gcloud sql databases create user_db --instance=user-db
   
   gcloud sql instances create template-db --database-version=POSTGRES_15 --tier=db-f1-micro
   gcloud sql databases create template_db --instance=template-db
   ```

3. **Create Memorystore Redis:**
   ```bash
   gcloud redis instances create notification-redis --size=1 --region=us-central1
   ```

4. **Deploy to Cloud Run:**
   ```bash
   # For each service
   gcloud run deploy notification-api-gateway \
     --source . \
     --platform managed \
     --region us-central1 \
     --set-env-vars DATABASE_URL=...,RABBITMQ_URL=...
   ```

5. **Use Cloud Build for CI/CD:**
   ```yaml
   # cloudbuild.yaml
   steps:
     - name: 'gcr.io/cloud-builders/docker'
       args: ['build', '-f', 'services/api_gateway/Dockerfile', '-t', 'gcr.io/$PROJECT_ID/api-gateway', '.']
     - name: 'gcr.io/cloud-builders/docker'
       args: ['push', 'gcr.io/$PROJECT_ID/api-gateway']
     - name: 'gcr.io/cloud-builders/gcloud'
       args: ['run', 'deploy', 'api-gateway', '--image', 'gcr.io/$PROJECT_ID/api-gateway']
   ```

### Pros:
- ✅ Serverless (pay per use)
- ✅ Auto-scaling
- ✅ Integrated with GCP services
- ✅ Good free tier

### Cons:
- ❌ Cold starts possible
- ❌ Vendor lock-in
- ❌ Need to adapt to Pub/Sub if not using RabbitMQ

---

## Option 6: Kubernetes (Production)

**Best for:** Enterprise deployments, maximum control, high scale.

### Architecture:

- **Kubernetes cluster** (EKS, GKE, or AKS)
- **PostgreSQL** (StatefulSet or managed service)
- **Redis** (StatefulSet or managed service)
- **RabbitMQ** (StatefulSet or Helm chart)
- **Ingress Controller** (NGINX, Traefik)
- **Service Mesh** (optional: Istio, Linkerd)

### Steps:

1. **Create Kubernetes manifests** for:
   - Deployments (each service)
   - Services (ClusterIP)
   - ConfigMaps (non-sensitive config)
   - Secrets (sensitive data)
   - Ingress (routing)

2. **Example Deployment:**
   ```yaml
   # k8s/api-gateway-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: api-gateway
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: api-gateway
     template:
       metadata:
         labels:
           app: api-gateway
       spec:
         containers:
         - name: api-gateway
           image: your-registry/api-gateway:latest
           ports:
           - containerPort: 8000
           env:
           - name: DATABASE_URL
             valueFrom:
               secretKeyRef:
                 name: notification-secrets
                 key: database-url
   ```

3. **Deploy:**
   ```bash
   kubectl apply -f k8s/
   ```

4. **Set up monitoring:**
   - Prometheus + Grafana
   - ELK Stack for logging

### Pros:
- ✅ Maximum flexibility
- ✅ Industry standard
- ✅ Excellent scaling
- ✅ Multi-cloud capable

### Cons:
- ❌ Very complex
- ❌ Requires expertise
- ❌ Higher operational overhead

---

## Option 7: DigitalOcean App Platform

**Best for:** Simple production deployments with managed infrastructure.

### Steps:

1. **Create App Platform app** from GitHub

2. **Add databases:**
   - PostgreSQL (User DB)
   - PostgreSQL (Template DB)
   - Redis

3. **Add services:**
   - For each microservice, create a new component
   - Set Dockerfile path
   - Configure environment variables

4. **Add RabbitMQ:**
   - Use a Droplet with Docker or managed service

### Pros:
- ✅ Simple interface
- ✅ Good pricing
- ✅ Managed databases

### Cons:
- ❌ Less flexible than AWS/GCP
- ❌ Smaller ecosystem

---

## Environment Variables

### Required for All Services:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
POSTGRES_USER_PASSWORD=strong-password
POSTGRES_TEMPLATE_PASSWORD=strong-password

# Message Queue
RABBITMQ_URL=amqp://user:pass@host:5672/
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=strong-password

# Cache
REDIS_URL=redis://host:6379/0

# Security
JWT_SECRET=generate-strong-random-secret-here
SERVICE_TOKEN=internal-service-authentication-token
```

### Service-Specific:

**API Gateway:**
```bash
USER_SERVICE_URL=http://user-service:8000
TEMPLATE_SERVICE_URL=http://template-service:8000
```

**Email Service:**
```bash
SENDGRID_API_KEY=SG.xxxxx
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-key
EMAIL_FROM=noreply@yourdomain.com
```

**Push Service:**
```bash
FCM_PROJECT_ID=your-project-id
FCM_SERVICE_ACCOUNT_PATH=/app/notification-service-d10e6-c3b98cba24f9.json
```

---

## Post-Deployment Checklist

- [ ] All services are healthy (check `/health` endpoints)
- [ ] Database migrations completed
- [ ] Test users created
- [ ] Templates initialized
- [ ] Environment variables configured correctly
- [ ] SSL certificates active
- [ ] Monitoring and logging set up
- [ ] Backup strategy configured
- [ ] Rate limiting configured
- [ ] CORS settings updated for production
- [ ] API documentation accessible
- [ ] Load testing performed
- [ ] Security audit completed
- [ ] Disaster recovery plan documented

---

## Recommended Production Setup

For a production deployment, we recommend:

1. **Platform:** **Render.com (Starter/Standard plans)** or AWS ECS/Fargate or GCP Cloud Run
2. **Database:** Managed PostgreSQL (Render, RDS, or Cloud SQL) with automated backups
3. **Cache:** Managed Redis (Render, ElastiCache, or Memorystore)
4. **Message Queue:** RabbitMQ on Render, Amazon MQ, or Cloud Pub/Sub
5. **Monitoring:** Render's built-in monitoring, CloudWatch / Stackdriver + Prometheus
6. **CI/CD:** Render's automatic deployments from Git, or GitHub Actions / GitLab CI
7. **CDN:** CloudFront or Cloud CDN for static assets
8. **WAF:** AWS WAF or Cloud Armor for security (if using AWS/GCP)

---

## Cost Estimation (Monthly)

| Platform | Small Scale | Medium Scale | Large Scale |
|----------|------------|--------------|-------------|
| Render (Free) | $0 | - | - |
| Render (Paid) | $25-50 | $100-200 | $500+ |
| Railway | $20-40 | $80-150 | $400+ |
| AWS | $50-100 | $200-500 | $1000+ |
| GCP | $30-60 | $150-400 | $800+ |
| DigitalOcean | $25-50 | $100-250 | $600+ |

*Estimates are approximate and depend on traffic, storage, and compute needs.*

---

## Need Help?

- Check service logs: `docker-compose logs -f <service-name>`
- Test endpoints: `curl http://localhost:8000/health`
- Verify RabbitMQ: Access management UI at port 15672
- Check database connections: Use `psql` or database client

---

## Security Best Practices

1. **Never commit secrets** - Use environment variables or secret managers
2. **Use strong passwords** - Generate random strings for all credentials
3. **Enable SSL/TLS** - Always use HTTPS in production
4. **Implement rate limiting** - Protect against abuse
5. **Regular updates** - Keep dependencies and base images updated
6. **Network security** - Use VPCs, security groups, and firewalls
7. **Backup regularly** - Automated backups for databases
8. **Monitor access** - Log all authentication attempts
9. **Use service tokens** - For inter-service communication
10. **Rotate secrets** - Regularly update API keys and passwords

