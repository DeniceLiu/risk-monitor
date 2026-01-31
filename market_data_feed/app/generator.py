"""Market data generator using Python generator pattern.

Memory-efficient O(1) implementation that yields one row at a time.
"""

import csv
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Generator, Dict, Any, Optional

logger = logging.getLogger(__name__)


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse timestamp from CSV.

    Supports formats:
    - ISO format: 2026-01-28T10:00:00
    - Date only: 2026-01-28
    - Unix milliseconds: 1706486400000
    """
    # Try ISO format first
    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        pass

    # Try date only
    try:
        return datetime.strptime(timestamp_str, "%Y-%m-%d")
    except ValueError:
        pass

    # Try unix milliseconds
    try:
        ts = int(timestamp_str)
        return datetime.fromtimestamp(ts / 1000)
    except (ValueError, OSError):
        pass

    raise ValueError(f"Cannot parse timestamp: {timestamp_str}")


def format_kafka_message(row: Dict[str, str], timestamp: datetime) -> Dict[str, Any]:
    """Format a CSV row as a Kafka message.

    Expected CSV columns:
    - timestamp: When the data was recorded
    - curve_type: USD_SOFR, USD_LIBOR, etc.
    - 2Y, 5Y, 10Y, 30Y: Rate values at each tenor

    Output format:
    {
        "timestamp": 1706486400000,  # Unix epoch milliseconds
        "curve_date": "2026-01-28",
        "curve_type": "USD_SOFR",
        "rates": {
            "2Y": 0.0410,
            "5Y": 0.0430,
            "10Y": 0.0450,
            "30Y": 0.0470
        }
    }
    """
    # Standard tenor columns
    tenor_columns = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

    rates = {}
    for tenor in tenor_columns:
        if tenor in row and row[tenor]:
            try:
                rates[tenor] = float(row[tenor])
            except ValueError:
                continue

    return {
        "timestamp": int(timestamp.timestamp() * 1000),
        "curve_date": timestamp.strftime("%Y-%m-%d"),
        "curve_type": row.get("curve_type", "USD_SOFR"),
        "rates": rates,
    }


def market_data_generator(
    file_path: str,
    replay_speed: float = 1.0,
    loop_forever: bool = False,
) -> Generator[Dict[str, Any], None, None]:
    """Generate market data snapshots from CSV file.

    This generator reads one row at a time, maintaining O(1) memory usage
    regardless of file size.

    Args:
        file_path: Path to CSV file with yield curve data
        replay_speed: Speed multiplier (1.0 = real-time, 10.0 = 10x faster)
        loop_forever: If True, restart from beginning when file ends

    Yields:
        Dict with formatted market data message

    Example:
        >>> for msg in market_data_generator("data/curves.csv", replay_speed=10.0):
        ...     producer.produce(topic, value=json.dumps(msg))
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    iteration = 0
    while True:
        iteration += 1
        logger.info(f"Starting data replay (iteration {iteration})")

        with open(path, "r", newline="") as f:
            reader = csv.DictReader(f)
            prev_timestamp: Optional[datetime] = None
            row_count = 0

            for row in reader:
                # Parse timestamp
                try:
                    current_timestamp = parse_timestamp(row["timestamp"])
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping row with invalid timestamp: {e}")
                    continue

                # Calculate sleep duration based on time delta
                if prev_timestamp is not None:
                    time_delta = (current_timestamp - prev_timestamp).total_seconds()
                    if time_delta > 0 and replay_speed > 0:
                        sleep_duration = time_delta / replay_speed
                        # Cap maximum sleep to prevent very long waits
                        sleep_duration = min(sleep_duration, 60.0)
                        if sleep_duration > 0.001:  # Only sleep if > 1ms
                            time.sleep(sleep_duration)

                # Format and yield message
                message = format_kafka_message(row, current_timestamp)
                yield message

                prev_timestamp = current_timestamp
                row_count += 1

                if row_count % 100 == 0:
                    logger.debug(f"Processed {row_count} rows")

        logger.info(f"Completed replay of {row_count} rows")

        if not loop_forever:
            break

        # Small delay before restarting
        logger.info("Restarting from beginning...")
        time.sleep(1.0)
