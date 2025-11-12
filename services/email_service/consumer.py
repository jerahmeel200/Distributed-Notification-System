"""
Email Service RabbitMQ Consumer
"""
import pika
import json
import os
import sys
import asyncio
from typing import Dict

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.logger import get_logger, set_correlation_id
from shared.retry import retry_with_backoff
from shared.circuit_breaker import CircuitBreaker
from sender import EmailSender
from http_client import HTTPClient

logger = get_logger(__name__)


class EmailConsumer:
    def __init__(self):
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        self.template_service_url = os.getenv("TEMPLATE_SERVICE_URL", "http://localhost:8004")
        self.user_service_url = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
        self.email_sender = EmailSender()
        self.http_client = HTTPClient()
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

    def connect(self):
        """Connect to RabbitMQ"""
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            # Declare exchange and queues
            channel.exchange_declare(exchange="notifications.direct", exchange_type="direct", durable=True)
            
            # Email queue
            channel.queue_declare(queue="email.queue", durable=True)
            channel.queue_bind(exchange="notifications.direct", queue="email.queue", routing_key="email")
            
            # Dead letter queue
            channel.queue_declare(queue="failed.queue", durable=True)

            return connection, channel
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def process_message(self, ch, method, properties, body):
        """Process email notification message"""
        message = None
        request_id = "unknown"
        try:
            message = json.loads(body)
            request_id = message.get("request_id", "unknown")
            set_correlation_id(request_id)

            logger.info(f"Processing email notification: {request_id}")

            # Check idempotency (would use Redis in production)
            # For now, process directly

            # Get user data
            user_id = message.get("user_id")
            user_data = self.http_client.get_user(user_id)
            if not user_data or not user_data.get("email"):
                raise Exception(f"User {user_id} not found or has no email")

            # Check user preferences
            if not user_data.get("email_enabled", True):
                logger.info(f"User {user_id} has email disabled")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Get template
            template_code = message.get("template_code")
            template = self.http_client.get_template(template_code)
            if not template:
                raise Exception(f"Template {template_code} not found")

            # Render template
            variables = message.get("variables", {})
            rendered = self.http_client.render_template(template_code, variables)
            if not rendered:
                raise Exception("Failed to render template")

            # Send email
            def send_email():
                return self.email_sender.send(
                    to_email=user_data["email"],
                    subject=rendered["subject"],
                    body=rendered["body"]
                )

            # Use circuit breaker and retry
            result = self.circuit_breaker.call(send_email)
            
            if result:
                logger.info(f"Email sent successfully: {request_id}")
                # Update status via API Gateway
                self.http_client.update_notification_status(
                    request_id,
                    "delivered"
                )
            else:
                raise Exception("Failed to send email")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"Error processing email: {e}")
            # Update status to failed
            try:
                if message:
                    request_id = message.get("request_id", request_id)
                self.http_client.update_notification_status(
                    request_id,
                    "failed",
                    error=str(e)
                )
            except:
                pass
            
            # Retry logic - reject and requeue up to 3 times
            retry_count = properties.headers.get("x-retry-count", 0) if properties.headers else 0
            
            if retry_count < 3:
                # Requeue with retry count
                properties.headers = properties.headers or {}
                properties.headers["x-retry-count"] = retry_count + 1
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            else:
                # Move to dead letter queue
                logger.error(f"Moving message to DLQ after {retry_count} retries: {request_id}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                # Publish to failed queue
                ch.basic_publish(
                    exchange="notifications.direct",
                    routing_key="failed",
                    body=body,
                    properties=pika.BasicProperties(delivery_mode=2)
                )

    async def start_consuming(self):
        """Start consuming messages from queue"""
        import threading
        
        def consume():
            """Blocking consumer in separate thread"""
            while True:
                try:
                    connection, channel = self.connect()
                    logger.info("Email consumer connected to RabbitMQ")

                    channel.basic_qos(prefetch_count=10)
                    channel.basic_consume(
                        queue="email.queue",
                        on_message_callback=self.process_message
                    )

                    channel.start_consuming()
                except Exception as e:
                    logger.error(f"Consumer error: {e}, retrying in 5 seconds...")
                    import time
                    time.sleep(5)
        
        # Run blocking consumer in thread
        thread = threading.Thread(target=consume, daemon=True)
        thread.start()

