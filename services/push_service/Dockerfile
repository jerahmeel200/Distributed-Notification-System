FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/push_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/push_service /app

# Copy shared utilities
COPY shared /app/shared

# Copy FCM service account file (optional - can also use volume mount in docker-compose.yml)
# If file doesn't exist, build will fail - use volume mount in docker-compose.yml instead
COPY notification-service-d10e6-c3b98cba24f9.json /app/notification-service-d10e6-c3b98cba24f9.json

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

