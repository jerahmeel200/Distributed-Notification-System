"""
RabbitMQ Queue Manager
"""
import pika
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.logger import get_logger

logger = get_logger(__name__)


class QueueManager:
    def __init__(self):
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        self.connection = None
        self.channel = None

    def initialize(self):
        """Initialize RabbitMQ connection and setup queues"""
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare exchange
            self.channel.exchange_declare(
                exchange="notifications.direct",
                exchange_type="direct",
                durable=True
            )

            # Declare queues
            self.channel.queue_declare(queue="email.queue", durable=True)
            self.channel.queue_declare(queue="push.queue", durable=True)
            self.channel.queue_declare(queue="failed.queue", durable=True)

            # Bind queues to exchange
            self.channel.queue_bind(
                exchange="notifications.direct",
                queue="email.queue",
                routing_key="email"
            )
            self.channel.queue_bind(
                exchange="notifications.direct",
                queue="push.queue",
                routing_key="push"
            )

            logger.info("Queue manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize queue manager: {e}")
            raise

    def publish(self, routing_key: str, message: dict):
        """Publish message to queue"""
        try:
            if not self.channel or self.channel.is_closed:
                self.initialize()

            self.channel.basic_publish(
                exchange="notifications.direct",
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type="application/json"
                )
            )
            logger.info(f"Message published to {routing_key} queue")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

