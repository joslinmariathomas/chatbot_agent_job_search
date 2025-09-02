import logging
import signal
import sys
from kafka_producer_consumer.kafka_consumer import start_consumers
from kafka_topics_consumers import parsed_job_processor
from kafka_producer_consumer.config import BOOTSTRAP_SERVERS
from utils.feature_extractor.extract_job_details import JobRequirementsExtractor
from utils.vector_storage.qdrant_storage import QdrantStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConsumerApp:
    def __init__(
        self,
        feature_extractor_rqmt: JobRequirementsExtractor,
        vector_storage_rqmt: QdrantStorage,
        bootstrap_servers: str = BOOTSTRAP_SERVERS,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.feature_extractor = feature_extractor_rqmt
        self.vector_storage = vector_storage_rqmt
        self.running = True

    def setup_signal_handlers(self):
        """Handle graceful shutdown on SIGINT/SIGTERM"""
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum, frame):
        """Graceful shutdown handler"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        sys.exit(0)

    def run(self):
        """Main consumer loop"""
        self.setup_signal_handlers()
        logger.info("Starting Kafka consumer service...")

        try:
            job_processor = parsed_job_processor(
                feature_extractor=self.feature_extractor,
                vector_storage=self.vector_storage,
            )
            start_consumers([job_processor], self.bootstrap_servers)

        except Exception as e:
            logger.error(f"Consumer app failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    feature_extractor = JobRequirementsExtractor()
    vector_storage = QdrantStorage()
    app = ConsumerApp(
        feature_extractor_rqmt=feature_extractor,
        vector_storage_rqmt=vector_storage,
    )
    app.run()
