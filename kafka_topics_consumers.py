from utils.feature_extractor.extract_job_details import JobRequirementsExtractor
from utils.feature_extractor.feature_extractor_consumer import FeatureExtractorProcessor
from utils.vector_storage.qdrant_storage import QdrantStorage

# KAFKA TOPICS
PARSED_JOB_TOPIC = "parsed_job.topic"


# KAFKA CONSUMERS
PARSED_JOB_FEATURE_EXTRACTOR = "parsed_job.feature_extractor.consumer"


# MESSAGE_PROCESSORS
def parsed_job_processor(
    feature_extractor: JobRequirementsExtractor,
    vector_storage: QdrantStorage,
):

    processor = FeatureExtractorProcessor(
        topic_name=PARSED_JOB_TOPIC,
        consumer_id="PARSED_JOB_FEATURE_EXTRACTOR",
        job_requirements=feature_extractor,
        vector_storage=vector_storage,
    )
    return processor
