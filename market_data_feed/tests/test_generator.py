"""Tests for market data generator."""

import tempfile
import pytest
from datetime import datetime

from app.generator import (
    parse_timestamp,
    format_kafka_message,
    market_data_generator,
)


class TestParseTimestamp:
    """Tests for timestamp parsing."""

    def test_parse_iso_format(self):
        """Test parsing ISO format timestamp."""
        result = parse_timestamp("2026-01-28T10:00:00")
        assert result == datetime(2026, 1, 28, 10, 0, 0)

    def test_parse_date_only(self):
        """Test parsing date-only format."""
        result = parse_timestamp("2026-01-28")
        assert result == datetime(2026, 1, 28, 0, 0, 0)

    def test_parse_unix_milliseconds(self):
        """Test parsing Unix milliseconds."""
        # 2026-01-28 00:00:00 UTC
        result = parse_timestamp("1769558400000")
        assert result.year == 2026
        assert result.month == 1

    def test_parse_invalid_raises(self):
        """Test that invalid timestamps raise ValueError."""
        with pytest.raises(ValueError):
            parse_timestamp("not-a-timestamp")


class TestFormatKafkaMessage:
    """Tests for message formatting."""

    def test_format_basic_message(self):
        """Test formatting a basic message."""
        row = {
            "timestamp": "2026-01-28T10:00:00",
            "curve_type": "USD_SOFR",
            "2Y": "0.0420",
            "5Y": "0.0410",
            "10Y": "0.0420",
            "30Y": "0.0450",
        }
        timestamp = datetime(2026, 1, 28, 10, 0, 0)

        result = format_kafka_message(row, timestamp)

        assert result["curve_type"] == "USD_SOFR"
        assert result["curve_date"] == "2026-01-28"
        assert result["rates"]["2Y"] == 0.0420
        assert result["rates"]["5Y"] == 0.0410
        assert result["rates"]["10Y"] == 0.0420
        assert result["rates"]["30Y"] == 0.0450
        assert "timestamp" in result

    def test_format_skips_invalid_rates(self):
        """Test that invalid rate values are skipped."""
        row = {
            "curve_type": "USD_SOFR",
            "2Y": "0.0420",
            "5Y": "invalid",
            "10Y": "",
        }
        timestamp = datetime(2026, 1, 28, 10, 0, 0)

        result = format_kafka_message(row, timestamp)

        assert "2Y" in result["rates"]
        assert "5Y" not in result["rates"]
        assert "10Y" not in result["rates"]

    def test_format_default_curve_type(self):
        """Test default curve type when not specified."""
        row = {"2Y": "0.0420"}
        timestamp = datetime(2026, 1, 28, 10, 0, 0)

        result = format_kafka_message(row, timestamp)

        assert result["curve_type"] == "USD_SOFR"


class TestMarketDataGenerator:
    """Tests for the generator function."""

    def test_generator_yields_messages(self):
        """Test that generator yields formatted messages."""
        csv_content = """timestamp,curve_type,2Y,5Y,10Y,30Y
2026-01-28T10:00:00,USD_SOFR,0.0420,0.0410,0.0420,0.0450
2026-01-28T10:00:01,USD_SOFR,0.0421,0.0411,0.0421,0.0451
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()

            messages = list(market_data_generator(f.name, replay_speed=1000, loop_forever=False))

            assert len(messages) == 2
            assert messages[0]["curve_type"] == "USD_SOFR"
            assert messages[0]["rates"]["2Y"] == 0.0420
            assert messages[1]["rates"]["2Y"] == 0.0421

    def test_generator_file_not_found(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            list(market_data_generator("/nonexistent/file.csv"))

    def test_generator_skips_invalid_rows(self):
        """Test that rows with invalid timestamps are skipped."""
        csv_content = """timestamp,curve_type,2Y,5Y
2026-01-28T10:00:00,USD_SOFR,0.0420,0.0410
invalid-timestamp,USD_SOFR,0.0421,0.0411
2026-01-28T10:00:02,USD_SOFR,0.0422,0.0412
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()

            messages = list(market_data_generator(f.name, replay_speed=1000, loop_forever=False))

            # Should skip the invalid row
            assert len(messages) == 2

    def test_generator_respects_replay_speed(self):
        """Test that replay speed affects timing (basic check)."""
        csv_content = """timestamp,curve_type,2Y
2026-01-28T10:00:00,USD_SOFR,0.0420
2026-01-28T10:00:01,USD_SOFR,0.0421
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()

            import time
            start = time.time()
            # Very fast replay
            list(market_data_generator(f.name, replay_speed=1000, loop_forever=False))
            elapsed = time.time() - start

            # Should complete almost instantly with 1000x speed
            assert elapsed < 1.0
