# =============================================================================
# kafka_producer.py — Kafka Event Publisher
# =============================================================================
# What this file does:
#   Publishes notification events to Kafka whenever something meaningful happens
#   in the API (trade offer created, password changed, etc.). The email service
#   runs separately and consumes those events to send emails — fully decoupled.
#
# Key decisions:
#   - Fire-and-forget: we don't wait for Kafka to confirm delivery before
#     returning an API response. This keeps the API fast even if Kafka is slow.
#   - producer.poll(0): Kafka queues delivery callbacks internally. poll() drains
#     that queue. Passing 0 makes it non-blocking — we just check for any waiting
#     callbacks without sleeping.
#   - Batching (queue.buffering.max.ms=1000): groups messages for up to 1 second
#     before sending. Better throughput at the cost of slight added latency.
#   - flush_kafka_producer on shutdown: called via atexit in main.py. Without
#     this, messages still in the buffer are silently lost when the process exits.
#
# Event flow:
#   API route → publish_notification_event() → Kafka topic "notifications"
#       → email_service consumer → SMTP email
# =============================================================================

from confluent_kafka import Producer
import json
from typing import Dict, Any
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

conf = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    'client.id': 'retro-games-api',
    'queue.buffering.max.messages': 10000,
    'queue.buffering.max.kbytes': 1048576,
    'queue.buffering.max.ms': 1000,
}

producer = Producer(conf)


def delivery_report(err, msg):
    if err is not None:
        logger.error(f'Message delivery failed: {err}')
    else:
        logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')


def publish_notification_event(event_type: str, data: Dict[str, Any]) -> bool:
    try:
        message = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'data': data
        }

        producer.produce(
            'notifications',
            value=json.dumps(message).encode('utf-8'),
            callback=delivery_report
        )

        producer.poll(0)

        logger.info(f'Published {event_type} event to Kafka')
        return True

    except Exception as e:
        logger.error(f'Failed to publish event: {e}', exc_info=True)
        return False


def flush_kafka_producer():
    logger.info('Flushing Kafka producer...')
    remaining = producer.flush(timeout=10)
    if remaining > 0:
        logger.warning(f'{remaining} messages were not delivered before shutdown')
    else:
        logger.info('Kafka producer flushed successfully')
