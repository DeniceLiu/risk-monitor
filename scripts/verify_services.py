#!/usr/bin/env python3
"""
Phase 1 Service Verification Script

Verifies all infrastructure services are running and accessible:
- PostgreSQL: Database connection and schema
- Redis: Connection and basic operations
- Kafka: Broker connection and topic creation

Usage:
    python scripts/verify_services.py
"""

import sys
import time
from typing import Tuple


def check_postgres() -> Tuple[bool, str]:
    """Verify PostgreSQL connection and schema."""
    try:
        import psycopg2

        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="risk_db",
            user="riskuser",
            password="riskpass"
        )

        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('instruments', 'bonds', 'interest_rate_swaps')
        """)
        tables = [row[0] for row in cursor.fetchall()]

        if len(tables) != 3:
            return False, f"Missing tables. Found: {tables}"

        # Check sample data
        cursor.execute("SELECT COUNT(*) FROM instruments")
        count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return True, f"Connected. Tables: {tables}. Instruments: {count}"

    except ImportError:
        return False, "psycopg2 not installed. Run: pip install psycopg2-binary"
    except Exception as e:
        return False, str(e)


def check_redis() -> Tuple[bool, str]:
    """Verify Redis connection and basic operations."""
    try:
        import redis

        r = redis.Redis(host='localhost', port=6379, decode_responses=True)

        # Test ping
        if not r.ping():
            return False, "Ping failed"

        # Test write/read
        r.set("_test_key", "test_value")
        value = r.get("_test_key")
        r.delete("_test_key")

        if value != "test_value":
            return False, "Write/read test failed"

        return True, "Connected. Read/write OK."

    except ImportError:
        return False, "redis not installed. Run: pip install redis"
    except Exception as e:
        return False, str(e)


def check_kafka() -> Tuple[bool, str]:
    """Verify Kafka broker connection."""
    try:
        from confluent_kafka.admin import AdminClient, NewTopic
        from confluent_kafka import KafkaException

        admin = AdminClient({'bootstrap.servers': 'localhost:9092'})

        # Get cluster metadata
        metadata = admin.list_topics(timeout=10)

        # Create test topic if it doesn't exist
        topic_name = "yield_curve_ticks"
        if topic_name not in metadata.topics:
            new_topic = NewTopic(topic_name, num_partitions=3, replication_factor=1)
            futures = admin.create_topics([new_topic])
            for topic, future in futures.items():
                try:
                    future.result()
                except KafkaException as e:
                    if "already exists" not in str(e):
                        return False, f"Failed to create topic: {e}"

        # Refresh metadata
        metadata = admin.list_topics(timeout=10)
        topics = list(metadata.topics.keys())

        return True, f"Connected. Broker: {metadata.brokers}. Topics: {topics}"

    except ImportError:
        return False, "confluent-kafka not installed. Run: pip install confluent-kafka"
    except Exception as e:
        return False, str(e)


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Risk Monitor - Phase 1 Service Verification")
    print("=" * 60)
    print()

    checks = [
        ("PostgreSQL", check_postgres),
        ("Redis", check_redis),
        ("Kafka", check_kafka),
    ]

    results = []

    for name, check_fn in checks:
        print(f"Checking {name}...", end=" ", flush=True)
        success, message = check_fn()
        status = "✓ OK" if success else "✗ FAILED"
        print(status)
        print(f"  {message}")
        print()
        results.append(success)

    print("=" * 60)

    if all(results):
        print("✓ All services are running correctly!")
        print()
        print("Phase 1 Complete. Ready for Phase 2 (Security Master API).")
        return 0
    else:
        print("✗ Some services failed verification.")
        print()
        print("Troubleshooting:")
        print("  1. Ensure Docker is running: docker ps")
        print("  2. Start services: docker-compose up -d")
        print("  3. Check logs: docker-compose logs [service-name]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
