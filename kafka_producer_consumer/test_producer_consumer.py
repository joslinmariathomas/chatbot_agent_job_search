import logging
from datetime import datetime
import random

from kafka_producer_consumer.kafka_consumer import (
    start_consumers,
)
from kafka_producer_consumer.kafka_producer import produce_kafka_messages
from kafka_producer_consumer.message_processor_class import AbstractMessageProcessor


def test_kafka_producer_consumer():

    data = {
        "timestamp": datetime.now().isoformat(),
        "sensor_id": f"sensor_{random.randint(1, 10)}",
        "temperature": round(random.uniform(18.0, 35.0), 2),
        "humidity": round(random.uniform(30.0, 80.0), 2),
        "pressure": round(random.uniform(1000.0, 1020.0), 2),
        "location": ["warehouse_a", "warehouse_b", "warehouse_c"],
    }

    produce_kafka_messages(topic_name="test_topic", messages=[data])
    processor = MessageProcessor(
        topic_name="test_topic", consumer_id=f"test_consumer_{random.randint(1, 10)}"
    )
    start_consumers(processors=[processor])


class MessageProcessor(AbstractMessageProcessor):

    def handle_message(self, message):
        """Process individual message"""
        try:
            # Your message processing logic here
            logging.info(f"Processing message: {message.value}")

        except Exception as e:
            logging.info(f"Error processing message: {e}")
            return False
