import logging
import uuid
from pathlib import Path
from typing import Optional

from qdrant_client import models, QdrantClient
from qdrant_client.models import Filter
from sentence_transformers import SentenceTransformer

from utils.vector_storage.config import QdrantClientServer, FILTER_CONDITIONS_BY_KEYS


class QdrantStorage:
    def __init__(
        self,
        collection_name: str = "test_collection",
        distance: str = models.Distance.COSINE,
        sentence_transformer_model: str = "all-MiniLM-L6-v2",
        client_server: str = QdrantClientServer,
    ):
        self.client = QdrantClient(url=client_server)
        self.collection_name = collection_name
        self.distance = distance

        # Ensure the model is downloaded locally to avoid meta tensor issues
        cache_dir = Path.home() / ".cache" / "torch" / "sentence_transformers"
        cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.encoder = SentenceTransformer(
                sentence_transformer_model,
                device="cpu",
                cache_folder=str(cache_dir),
                trust_remote_code=True,
            )
        except RuntimeError as e:
            logging.warning(f"Failed to load model on first attempt: {e}")
            # Force download by initializing from HuggingFace model first
            from transformers import AutoModel, AutoTokenizer

            AutoModel.from_pretrained(
                sentence_transformer_model, cache_dir=str(cache_dir)
            )
            AutoTokenizer.from_pretrained(
                sentence_transformer_model, cache_dir=str(cache_dir)
            )

            # Retry loading SentenceTransformer
            self.encoder = SentenceTransformer(
                sentence_transformer_model,
                device="cpu",
                cache_folder=str(cache_dir),
                trust_remote_code=True,
            )

        logging.info(
            f"Loaded SentenceTransformer model '{sentence_transformer_model}' on CPU"
        )

    def create_collection(self, create_indexes: bool = True):
        check_collection_exists = self.client.collection_exists(
            collection_name=self.collection_name
        )
        logging.info(
            f"Collection {self.collection_name} exists: {check_collection_exists}"
        )

        if not check_collection_exists:
            logging.info(f"Creating collection {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.encoder.get_sentence_embedding_dimension(),
                    distance=models.Distance.COSINE,
                ),
            )
            if create_indexes:
                job_search_indexes = [
                    ("job_position", "keyword"),
                    ("suburb", "keyword"),
                ]
                self.create_payload_indexes(job_search_indexes)

    def upload_points(
        self,
        points: list[dict],
        key_to_encode: str,
        given_ids: list = None,
    ):
        vectorised_points = self.structure_points(
            points=points, key_to_encode=key_to_encode
        )
        ids = (
            given_ids
            if given_ids and len(given_ids) == len(vectorised_points)
            else [str(uuid.uuid4()) for _ in vectorised_points]
        )
        payloads = self.get_payloads(points=points)
        self.client.upsert(
            collection_name=self.collection_name,
            points=models.Batch(
                payloads=payloads,
                vectors=vectorised_points,
                ids=ids,
            ),
        )

    def structure_points(self, points: list[dict], key_to_encode: str):
        vectorised_points = [
            self.encoder.encode(point[key_to_encode]).tolist() for point in points
        ]
        return vectorised_points

    def encode_query(self, query: str):
        return self.encoder.encode(query).tolist()

    def retrieve_docs_based_on_query(
        self,
        query: str,
        filter: Optional[dict[str:dict]] = None,
        limit: int = 3,
    ):
        encoded_query = self.encode_query(query)
        if not filter:
            hits = self.client.query_points(
                collection_name=self.collection_name,
                query=encoded_query,
                limit=limit,
            ).points
            return hits
        must_filter = self.create_filters(filter)
        hits = self.client.query_points(
            collection_name=self.collection_name,
            query=encoded_query,
            query_filter=models.Filter(must=must_filter),
            limit=limit,
        ).points
        return hits

    @staticmethod
    def get_payloads(points: list[dict]) -> list[dict]:
        return [{key: value for key, value in point.items()} for point in points]

    def create_payload_indexes(self, index_fields: list[tuple[str, str]]):
        """
        Create payload indexes for specified fields.

        Args:
            index_fields: List of tuples containing (field_name, field_type)
                         e.g., [("job_position", "keyword"), ("suburb", "keyword")]
        """
        for field_name, field_type in index_fields:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_type,
                )
                logging.info(
                    f"Created payload index for field '{field_name}' with type '{field_type}'"
                )
            except Exception as e:
                logging.warning(f"Failed to create index for field '{field_name}': {e}")

    @staticmethod
    def create_filters(filters: Optional[dict[str:dict]]):
        if "must" in filters:
            must_filters = []
            for key, value in filters["must"].items():
                must_filters.append(models.FieldCondition(key=key, match=value))
            return must_filters
        return None

    @staticmethod
    def create_filters_by_must_should_keywords(
        keyword_filters: Optional[dict[str, str]],
    ) -> dict:
        combined_filters = {}
        for filter_type in ["must", "should"]:
            filter_list = []
            keys_to_filter = FILTER_CONDITIONS_BY_KEYS.get(filter_type, [])
            for key in keys_to_filter:
                if keyword_filters.get(key) is not None:
                    if key == "url":
                        filter_list.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchValue(value=keyword_filters[key]),
                            )
                        )
                    else:
                        filter_list.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchText(text=keyword_filters[key]),
                            )
                        )
            combined_filters[filter_type] = filter_list
        return combined_filters

    def retrieve_docs_based_on_keyword_filters(
        self, keyword_filters: dict[str:dict]
    ) -> str:
        filters = self.create_filters_by_must_should_keywords(keyword_filters)
        result = self.client.scroll(
            collection_name="parsed_job.topic",
            scroll_filter=models.Filter(
                must=filters.get("must", []),
                should=filters.get("should", []),
            ),
            limit=3,
        )
        interested_job_description = result[0][0].payload.get(
            "description"
        )  # Implement multiple matches and response later
        return interested_job_description
