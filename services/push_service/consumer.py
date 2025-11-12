"""
Push Service RabbitMQ Consumer
"""
import pika
import json
import os
import sys
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.logger import get_logger, set_correlation_id
from shared.circuit_breaker import CircuitBreaker
from sender import PushSender
from http_client import HTTPClient

logger = get_logger(__name__)


class PushConsumer:
    def __init__(self):
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        self.template_service_url = os.getenv("TEMPLATE_SERVICE_URL", "http://localhost:8004")
        self.user_service_url = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
        self.push_sender = PushSender()
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
            
            # Push queue
            channel.queue_declare(queue="push.queue", durable=True)
            channel.queue_bind(exchange="notifications.direct", queue="push.queue", routing_key="push")
            
            # Dead letter queue
            channel.queue_declare(queue="failed.queue", durable=True)

            return connection, channel
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def process_message(self, ch, method, properties, body):
        """Process push notification message"""
        message = None
        request_id = "unknown"
        try:
            message = json.loads(body)
            request_id = message.get("request_id", "unknown")
            set_correlation_id(request_id)

            logger.info(f"Processing push notification: {request_id}")

            # Get user data
            user_id = message.get("user_id")
            user_data = self.http_client.get_user(user_id)
            if not user_data:
                raise Exception(f"User {user_id} not found")

            # Check user preferences
            if not user_data.get("push_enabled", True):
                logger.info(f"User {user_id} has push disabled")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            push_token = user_data.get("push_token")
            if not push_token:
                raise Exception(f"User {user_id} has no push token")

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

            # Send push notification
            def send_push():
                return self.push_sender.send(
                    token=push_token,
                    title=rendered.get("subject", "Notification"),
                    body=rendered.get("body", ""),
                    data=message.get("metadata", {})
                )

            # Use circuit breaker
            result = self.circuit_breaker.call(send_push)
            
            if result:
                logger.info(f"Push notification sent successfully: {request_id}")
                self.http_client.update_notification_status(
                    request_id,
                    "delivered"
                )
            else:
                raise Exception("Failed to send push notification")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"Error processing push: {e}")
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
            
            retry_count = properties.headers.get("x-retry-count", 0) if properties.headers else 0
            
            if retry_count < 3:
                properties.headers = properties.headers or {}
                properties.headers["x-retry-count"] = retry_count + 1
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            else:
                logger.error(f"Moving message to DLQ after {retry_count} retries: {request_id}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
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
                    logger.info("Push consumer connected to RabbitMQ")

                    channel.basic_qos(prefetch_count=10)
                    channel.basic_consume(
                        queue="push.queue",
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

