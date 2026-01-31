"""Market Data Feed - Main entry point."""

import logging
import signal
import sys
from pathlib import Path

from app.config import settings
from app.generator import market_data_generator
from app.producer import MarketDataProducer

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


def main():
    """Main entry point."""
    global shutdown_requested

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 60)
    logger.info("Market Data Feed Starting")
    logger.info("=" * 60)
    logger.info(f"Kafka: {settings.kafka_bootstrap_servers}")
    logger.info(f"Topic: {settings.kafka_topic}")
    logger.info(f"Data file: {settings.data_file}")
    logger.info(f"Replay speed: {settings.replay_speed}x")
    logger.info(f"Loop forever: {settings.loop_forever}")
    logger.info("=" * 60)

    # Resolve data file path
    data_file = Path(settings.data_file)
    if not data_file.is_absolute():
        # Try relative to current directory, then parent
        if not data_file.exists():
            parent_path = Path(__file__).parent.parent.parent / settings.data_file
            if parent_path.exists():
                data_file = parent_path

    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}")
        sys.exit(1)

    # Initialize producer
    producer = MarketDataProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        topic=settings.kafka_topic,
    )

    # Start generating and producing
    message_count = 0
    try:
        generator = market_data_generator(
            file_path=str(data_file),
            replay_speed=settings.replay_speed,
            loop_forever=settings.loop_forever,
        )

        for message in generator:
            if shutdown_requested:
                logger.info("Shutdown requested, stopping generator...")
                break

            producer.produce(message)
            message_count += 1

            if message_count % 10 == 0:
                logger.info(
                    f"Published {message_count} messages | "
                    f"Latest: {message['curve_type']} @ {message['curve_date']}"
                )

    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)

    finally:
        # Ensure all messages are delivered
        producer.close()
        logger.info(f"Total messages published: {message_count}")
        logger.info("Market Data Feed stopped")


if __name__ == "__main__":
    main()
