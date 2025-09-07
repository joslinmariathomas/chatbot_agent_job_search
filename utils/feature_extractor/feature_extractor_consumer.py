import json

from kafka.consumer.fetcher import ConsumerRecord

from kafka_producer_consumer.message_processor_classes.message_processor_class import (
    AbstractMessageProcessor,
)
from utils.feature_extractor.extract_job_details import JobRequirementsExtractor
from utils.vector_storage.qdrant_storage import QdrantStorage


class FeatureExtractorProcessor(AbstractMessageProcessor):
    def __init__(
        self,
        topic_name: str,
        consumer_id: str,
        job_requirements: JobRequirementsExtractor,
        vector_storage: QdrantStorage,
    ):
        super().__init__(topic_name=topic_name, consumer_id=consumer_id)
        self.job_requirements = job_requirements
        self.vector_storage = vector_storage

    def handle_message(self, message: ConsumerRecord):
        job_data = json.loads(message.value)
        extracted_job_dict = self.job_requirements.extract_requirements(
            job_description=job_data.get("description"),
        )
        combined_job_details_dict = {**job_data, **extracted_job_dict}
        if combined_job_details_dict:
            self.save_to_qdrant(
                job_listings=[combined_job_details_dict],
            )

    def save_to_qdrant(
        self,
        job_listings: list[dict],
    ):
        self.vector_storage.create_collection(collection_name=self.topic_name)
        self.vector_storage.upload_points(
            points=job_listings,
            key_to_encode="description",
            collection_name=self.topic_name,
        )
