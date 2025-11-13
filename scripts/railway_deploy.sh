#!/usr/bin/env bash

# Deploy all microservices to Railway using the CLI.
# Requires the following environment variables to be defined:
#   RAILWAY_TOKEN
#   RAILWAY_API_GATEWAY_SERVICE_ID
#   RAILWAY_USER_SERVICE_ID
#   RAILWAY_TEMPLATE_SERVICE_ID
#   RAILWAY_EMAIL_SERVICE_ID
#   RAILWAY_PUSH_SERVICE_ID
#   RAILWAY_RABBITMQ_SERVICE_ID   (if RabbitMQ runs as a Railway service)
#   RAILWAY_REDIS_SERVICE_ID      (if Redis runs as a Railway service)
#   RAILWAY_USER_DB_SERVICE_ID    (if using managed Postgres for user service)
#   RAILWAY_TEMPLATE_DB_SERVICE_ID (if using managed Postgres for template service)
#
# Any service IDs that are unset will be skipped automatically so you can
# gradually onboard services to Railway.

set -euo pipefail

if ! command -v railway >/dev/null 2>&1; then
  echo "railway CLI is required but was not found in PATH." >&2
  exit 1
fi

if [[ -z "${RAILWAY_TOKEN:-}" ]]; then
  echo "RAILWAY_TOKEN is not set; refusing to deploy." >&2
  exit 1
fi

deploy_service() {
  local service_id="$1"
  local label="$2"

  if [[ -z "${service_id}" ]]; then
    echo "Skipping ${label} (service id not provided)."
    return
  fi

  echo "::group::Deploying ${label}"
  railway up \
    --service "${service_id}" \
    --detach
  echo "::endgroup::"
}

deploy_service "${RAILWAY_RABBITMQ_SERVICE_ID:-}" "RabbitMQ"
deploy_service "${RAILWAY_REDIS_SERVICE_ID:-}" "Redis"
deploy_service "${RAILWAY_USER_DB_SERVICE_ID:-}" "User Postgres"
deploy_service "${RAILWAY_TEMPLATE_DB_SERVICE_ID:-}" "Template Postgres"
deploy_service "${RAILWAY_USER_SERVICE_ID:-}" "User Service"
deploy_service "${RAILWAY_TEMPLATE_SERVICE_ID:-}" "Template Service"
deploy_service "${RAILWAY_EMAIL_SERVICE_ID:-}" "Email Service"
deploy_service "${RAILWAY_PUSH_SERVICE_ID:-}" "Push Service"
deploy_service "${RAILWAY_API_GATEWAY_SERVICE_ID:-}" "API Gateway"

echo "Railway deployment finished."

