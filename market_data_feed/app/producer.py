"""Kafka producer for market data."""

import json
import logging
from typing import Optional, Callable

from confluent_kafka import Producer, KafkaError, KafkaException

logger = logging.getLogger(__name__)


def delivery_callback(err, msg):
    """Callback for message delivery reports."""
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")


class MarketDataProducer:
    """Kafka producer for market data messages."""

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        on_delivery: Optional[Callable] = None,
    ):
        """Initialize the producer.

        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Topic to produce to
            on_delivery: Optional delivery callback
        """
        self.topic = topic
        self.on_delivery = on_delivery or delivery_callback

        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "client.id": "market-data-feed",
            "acks": "all",  # Wait for all replicas
            "retries": 3,
            "retry.backoff.ms": 100,
            "linger.ms": 5,  # Batch messages for efficiency
            "batch.size": 16384,
            "compression.type": "snappy",
        })

        logger.info(f"Producer initialized: {bootstrap_servers} -> {topic}")

    def produce(self, message: dict) -> None:
        """Produce a message to Kafka.

        Args:
            message: Dictionary to serialize as JSON
        """
        try:
            # Use curve_type as key for partitioning
            key = message.get("curve_type", "default")

            self.producer.produce(
                topic=self.topic,
                key=key.encode("utf-8"),
                value=json.dumps(message).encode("utf-8"),
                callback=self.on_delivery,
            )

            # Trigger delivery callbacks
            self.producer.poll(0)

        except BufferError:
            logger.warning("Producer buffer full, waiting...")
            self.producer.poll(1.0)
            # Retry
            self.producer.produce(
                topic=self.topic,
                key=key.encode("utf-8"),
                value=json.dumps(message).encode("utf-8"),
                callback=self.on_delivery,
            )

        except KafkaException as e:
            logger.error(f"Kafka error: {e}")
            raise

    def flush(self, timeout: float = 10.0) -> int:
        """Flush all buffered messages.

        Args:
            timeout: Maximum time to wait

        Returns:
            Number of messages still in queue (0 if all delivered)
        """
        remaining = self.producer.flush(timeout)
        if remaining > 0:
            logger.warning(f"{remaining} messages still in queue after flush")
        return remaining

    def close(self) -> None:
        """Close the producer, flushing any remaining messages."""
        logger.info("Closing producer...")
        self.flush()
        logger.info("Producer closed")
