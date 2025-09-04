import threading
import time
import uuid
from unittest.mock import patch

from kafka_producer_consumer.kafka_consumer import start_consumers
from kafka_producer_consumer.kafka_producer import produce_kafka_messages
from utils.feature_extractor.extract_job_details import JobRequirementsExtractor
from utils.feature_extractor.feature_extractor_consumer import FeatureExtractorProcessor
from utils.vector_storage.qdrant_storage import QdrantStorage


@patch(
    "utils.feature_extractor.extract_job_details.JobRequirementsExtractor.extract_requirements"
)
def test_feature_extractor_consumer(mock_method):
    data = {
        "suburb": "North Sydney",
        "id": uuid.uuid4(),
        "job_position": None,
        "Company name": "oOh!",
        "description": "test_description",
    }
    topic_name = f"test_topic{uuid.uuid4()}"
    consumer_id = "test_consumer"
    vector_storage = QdrantStorage(client_server="http://localhost:6333")
    job_extractor = JobRequirementsExtractor()
    produce_kafka_messages(
        topic_name=topic_name, messages=[data], bootstrap_servers="localhost:9092"
    )
    mock_method.return_value = {"extracted_details": "data has been extracted"}
    processor = FeatureExtractorProcessor(
        topic_name=topic_name,
        consumer_id=consumer_id,
        vector_storage=vector_storage,
        job_requirements=job_extractor,
    )
    consumer_thread = threading.Thread(
        target=start_consumers, args=([processor], "localhost:9092"), daemon=True
    )
    consumer_thread.start()
    time.sleep(5)
    assert vector_storage.client.collection_exists(collection_name=topic_name)
    assert vector_storage.client.count(collection_name=topic_name).count == 1
    vector_storage.client.delete_collection(collection_name=topic_name)
