"""Risk Engine - Main entry point."""

import logging
import signal
import sys
import time
from typing import List, Union

from app.config import settings
from app.consumer import MarketDataConsumer, RedisWriter
from app.portfolio import load_portfolio
from app.pricing import YieldCurveBuilder, RiskCalculator
from app.pricing.instruments import BondData, SwapData

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


def process_market_update(
    message: dict,
    curve_builder: YieldCurveBuilder,
    risk_calculator: RiskCalculator,
    portfolio: List[Union[BondData, SwapData]],
    redis_writer: RedisWriter,
) -> int:
    """Process a single market data update.

    Args:
        message: Market data message from Kafka
        curve_builder: Yield curve builder
        risk_calculator: Risk calculator
        portfolio: List of instruments
        redis_writer: Redis writer

    Returns:
        Number of instruments processed
    """
    # Update yield curve
    curve_builder.update_rates(message["rates"], message["curve_date"])

    curve_timestamp = message["timestamp"]

    # Persist current yield curve snapshot for dashboard
    redis_writer.write_yield_curve(message["rates"], curve_timestamp)
    processed = 0

    # Calculate risk for each instrument
    for instrument in portfolio:
        try:
            metrics = risk_calculator.calculate(instrument)
            redis_writer.write_risk(metrics, curve_timestamp)
            processed += 1

        except Exception as e:
            logger.error(f"Failed to calculate risk for {instrument.id}: {e}")
            continue

    return processed


def aggregate_portfolio(redis_writer: RedisWriter) -> dict:
    """Aggregate portfolio risk metrics.

    Args:
        redis_writer: Redis writer with access to trade data

    Returns:
        Aggregated metrics
    """
    trade_risks = redis_writer.get_all_trade_risks()

    aggregates = {
        "total_npv": 0.0,
        "total_dv01": 0.0,
        "instrument_count": len(trade_risks),
        "krd": {"2Y": 0.0, "5Y": 0.0, "10Y": 0.0, "30Y": 0.0},
    }

    for instrument_id, data in trade_risks.items():
        try:
            aggregates["total_npv"] += float(data.get("npv", 0))
            aggregates["total_dv01"] += float(data.get("dv01", 0))

            for tenor in ["2y", "5y", "10y", "30y"]:
                krd_key = f"krd_{tenor}"
                if krd_key in data:
                    aggregates["krd"][tenor.upper()] += float(data[krd_key])

        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid data for {instrument_id}: {e}")
            continue

    return aggregates


def main():
    """Main entry point."""
    global shutdown_requested

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 60)
    logger.info(f"Risk Engine Starting (Worker: {settings.worker_id})")
    logger.info("=" * 60)
    logger.info(f"Kafka: {settings.kafka_bootstrap_servers}")
    logger.info(f"Topic: {settings.kafka_topic}")
    logger.info(f"Group: {settings.kafka_group_id}")
    logger.info(f"Redis: {settings.redis_host}:{settings.redis_port}")
    logger.info(f"Security Master: {settings.security_master_url}")
    logger.info("=" * 60)

    # Initialize components
    try:
        # Load portfolio from Security Master
        logger.info("Loading portfolio from Security Master...")
        portfolio = load_portfolio(settings.security_master_url)

        if not portfolio:
            logger.error("No instruments loaded, exiting")
            sys.exit(1)

        # Initialize curve builder and risk calculator
        curve_builder = YieldCurveBuilder()
        risk_calculator = RiskCalculator(curve_builder, settings.bump_size)

        # Initialize Redis writer
        redis_writer = RedisWriter(
            host=settings.redis_host,
            port=settings.redis_port,
            ttl=settings.redis_ttl,
        )

        # Initialize Kafka consumer
        consumer = MarketDataConsumer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_group_id,
            topic=settings.kafka_topic,
        )

    except Exception as e:
        logger.exception(f"Failed to initialize: {e}")
        sys.exit(1)

    # Main processing loop
    message_count = 0
    start_time = time.time()

    try:
        logger.info("Starting market data consumption...")

        for message in consumer.consume():
            if shutdown_requested:
                logger.info("Shutdown requested, stopping...")
                break

            try:
                # Process the market update
                processed = process_market_update(
                    message,
                    curve_builder,
                    risk_calculator,
                    portfolio,
                    redis_writer,
                )

                message_count += 1

                # Aggregate and log periodically
                if message_count % 5 == 0:
                    aggregates = aggregate_portfolio(redis_writer)
                    redis_writer.write_portfolio_aggregates(aggregates)

                    elapsed = time.time() - start_time
                    rate = message_count / elapsed if elapsed > 0 else 0

                    logger.info(
                        f"Processed {message_count} updates ({rate:.1f}/sec) | "
                        f"Instruments: {processed} | "
                        f"Portfolio DV01: ${aggregates['total_dv01']:,.0f}"
                    )

            except Exception as e:
                logger.exception(f"Error processing message: {e}")
                continue

    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")

    finally:
        # Clean up
        consumer.close()
        redis_writer.close()

        elapsed = time.time() - start_time
        logger.info(f"Processed {message_count} messages in {elapsed:.1f}s")
        logger.info("Risk Engine stopped")


if __name__ == "__main__":
    main()
