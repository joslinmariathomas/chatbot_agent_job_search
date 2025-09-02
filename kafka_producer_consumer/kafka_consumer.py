import logging
import threading
from typing import List

from kafka import KafkaConsumer

from kafka_producer_consumer.config import BOOTSTRAP_SERVERS
from kafka_producer_consumer.message_processor_classes.message_processor_class import (
    AbstractMessageProcessor,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def consume_kafka_messages(
    processor: AbstractMessageProcessor, bootstrap_servers: str = BOOTSTRAP_SERVERS
):
    if not check_broker_connectivity(bootstrap_servers=bootstrap_servers):
        logging.error("Cannot connect to broker, aborting...")
        return

    consumer = None
    try:
        consumer = KafkaConsumer(
            processor.topic_name,
            bootstrap_servers=bootstrap_servers,
            group_id=processor.consumer_id,
            auto_offset_reset="earliest",
            # Optimized settings for background processing
            max_poll_interval_ms=3000000,  # 5 minutes for heavy AI processing
            max_poll_records=5,  # Process small batches
            session_timeout_ms=30000,  # 30 seconds
            heartbeat_interval_ms=10000,  # 10 seconds
            enable_auto_commit=True,
            auto_commit_interval_ms=5000,  # Commit every 5 seconds
        )

        logging.info(f"Started consumer for topic: {processor.topic_name}")

        # Continuous polling loop
        while True:
            try:
                message_batch = consumer.poll(timeout_ms=1000)

                if not message_batch:
                    continue

                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            processor.handle_message(message)
                        except Exception as e:
                            logging.error(
                                f"Error processing message from {processor.topic_name}: {e}"
                            )

            except KeyboardInterrupt:
                logging.info("Received shutdown signal, closing consumer...")
                break

    except Exception as e:
        logging.error(f"Consumer error for {processor.topic_name}: {e}")
    finally:
        if consumer:
            consumer.close()
            logging.info(f"Closed consumer for topic: {processor.topic_name}")


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


def check_broker_connectivity(bootstrap_servers: str = BOOTSTRAP_SERVERS):
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=[bootstrap_servers],
            consumer_timeout_ms=5000,  # 5 second timeout
        )

        logging.info("Successfully connected to broker")
        logging.info(f"Available topics: {list(consumer.topics())}")

        consumer.close()
        return True

    except Exception as e:
        logging.info(f"Connection failed: {e}")
        return False
