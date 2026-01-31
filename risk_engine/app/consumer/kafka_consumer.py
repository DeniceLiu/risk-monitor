"""Kafka consumer for market data updates."""

import json
import logging
from typing import Generator, Dict, Any, Optional

from confluent_kafka import Consumer, KafkaError, KafkaException

logger = logging.getLogger(__name__)


class MarketDataConsumer:
    """Kafka consumer for yield curve updates."""

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topic: str,
    ):
        """Initialize the consumer.

        Args:
            bootstrap_servers: Kafka bootstrap servers
            group_id: Consumer group ID for load balancing
            topic: Topic to consume from
        """
        self.topic = topic

        self.consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "latest",
            "enable.auto.commit": False,  # Manual commit after processing
            "max.poll.interval.ms": 300000,  # 5 minutes
            "session.timeout.ms": 30000,
        })

        self.consumer.subscribe([topic])
        logger.info(f"Consumer initialized: {bootstrap_servers} <- {topic} (group: {group_id})")

    def consume(self, timeout: float = 1.0) -> Generator[Dict[str, Any], None, None]:
        """Consume messages from Kafka.

        Args:
            timeout: Poll timeout in seconds

        Yields:
            Parsed message dictionaries
        """
        try:
            while True:
                msg = self.consumer.poll(timeout)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"End of partition: {msg.partition()}")
                        continue
                    else:
                        raise KafkaException(msg.error())

                try:
                    value = json.loads(msg.value().decode("utf-8"))
                    yield value

                    # Commit after successful processing
                    self.consumer.commit(asynchronous=False)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message: {e}")
                    # Commit anyway to avoid reprocessing bad messages
                    self.consumer.commit(asynchronous=False)

        except KeyboardInterrupt:
            logger.info("Consumer interrupted")

    def close(self) -> None:
        """Close the consumer."""
        logger.info("Closing consumer...")
        self.consumer.close()
        logger.info("Consumer closed")
