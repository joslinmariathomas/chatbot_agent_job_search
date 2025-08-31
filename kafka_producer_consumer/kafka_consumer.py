import logging
import threading
from typing import List

from kafka import KafkaConsumer

from kafka_producer_consumer.config import BOOTSTRAP_SERVERS
from kafka_producer_consumer.message_processor_class import AbstractMessageProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def consume_kafka_messages(
    processor: AbstractMessageProcessor, bootstrap_servers: str = BOOTSTRAP_SERVERS
):
    consumer = None
    try:
        consumer = KafkaConsumer(
            processor.topic_name,
            bootstrap_servers=bootstrap_servers,
            group_id=processor.consumer_id,
            auto_offset_reset="earliest",
        )

        logger.info(f"Started consumer for topic: {processor.topic_name}")

        for message in consumer:
            try:
                processor.handle_message(message)
            except Exception as e:
                logger.error(
                    f"Error processing message from {processor.topic_name}: {e}"
                )
                # Continue processing other messages

    except Exception as e:
        logger.error(f"Consumer error for {processor.topic_name}: {e}")
    finally:
        if consumer:
            consumer.close()
            logger.info(f"Closed consumer for topic: {processor.topic_name}")


def start_consumers(
    processors: List[AbstractMessageProcessor],
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
):
    """Run multiple consumers concurrently (one per processor)."""
    if not processors:
        logger.warning("No processors provided")
        return

    threads = []

    try:
        for processor in processors:
            t = threading.Thread(
                target=consume_kafka_messages,
                args=(
                    processor,
                    bootstrap_servers,
                ),
                daemon=True,
                name=f"consumer-{processor.topic_name}",  # Give threads meaningful names
            )
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    except KeyboardInterrupt:
        logger.info("Shutting down consumers...")
