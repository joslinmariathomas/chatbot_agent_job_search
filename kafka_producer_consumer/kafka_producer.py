import json
import logging

from confluent_kafka.admin import AdminClient, NewTopic
from kafka import KafkaProducer

from kafka_producer_consumer.config import BOOTSTRAP_SERVERS


def produce_kafka_messages(topic_name: str, messages: list[dict]):
    create_topic_if_not_exists(topic_name=topic_name)
    producer = KafkaProducer(
        bootstrap_servers=[BOOTSTRAP_SERVERS],
        value_serializer=lambda x: (
            json.dumps(x, default=str).encode("utf-8") if x is not None else b"null"
        ),
        request_timeout_ms=30000,
        metadata_max_age_ms=30000,
    )
    for message in messages:
        try:
            producer.send(topic=topic_name, value=message)
        except Exception as e:
            logging.info(f"Failed to send message to topic {topic_name}")
    producer.close()


def create_topic_if_not_exists(
    topic_name: str, bootstrap_servers: str = BOOTSTRAP_SERVERS
):
    """Create topic using confluent-kafka library"""

    admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})
    try:
        metadata = admin_client.list_topics(timeout=10)

        if topic_name in metadata.topics:
            logging.info(f"Topic '{topic_name}' already exists")

        topic = NewTopic(topic_name, num_partitions=1, replication_factor=1)
        futures = admin_client.create_topics([topic])
        for topic, future in futures.items():
            try:
                future.result()
                logging.info(f"Topic '{topic}' created successfully")
            except Exception as e:
                logging.info(f"Failed to create topic '{topic}': {e}")
    except Exception as e:
        logging.info(f"Error creating topic: {e}")
