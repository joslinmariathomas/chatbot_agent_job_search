import logging
import uuid
from typing import Optional, Any

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import models, QdrantClient

from utils.vector_storage.config import QdrantClientServer, FILTER_CONDITIONS_BY_KEYS


class QdrantStorage:
    def __init__(
        self,
        distance: str = models.Distance.COSINE,
        sentence_transformer_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        sparse_embedding_model: str = "Qdrant/bm25",
        client_server: str = QdrantClientServer,
    ):
        self.client = QdrantClient(url=client_server)
        self.distance = distance
        self.encoder = TextEmbedding(sentence_transformer_model)
        self.sparse_encoder = SparseTextEmbedding(sparse_embedding_model)

    def create_collection(
        self,
        collection_name: str,
        create_indexes: bool = True,
    ):
        dense_embeddings = list(self.encoder.passage_embed("test_embeddings"))
        check_collection_exists = self.client.collection_exists(
            collection_name=collection_name
        )
        logging.info(f"Collection {collection_name} exists: {check_collection_exists}")

        if not check_collection_exists:
            logging.info(f"Creating collection {collection_name}")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "all-MiniLM-L6-v2": models.VectorParams(
                        size=len(dense_embeddings[0]),
                        distance=models.Distance.COSINE,
                    )
                },
                sparse_vectors_config={
                    "bm25": models.SparseVectorParams(
                        modifier=models.Modifier.IDF,
                    )
                },
            )
            if create_indexes:
                job_search_indexes = [
                    ("job_position", "keyword"),
                    ("suburb", "keyword"),
                ]
                self.create_payload_indexes(
                    collection_name=collection_name, index_fields=job_search_indexes
                )

    def upload_points(
        self,
        points: list[dict],
        key_to_encode: str,
        collection_name: str,
        given_ids: list = None,
    ):
        vectorised_points = self.structure_points(
            points=points, key_to_encode=key_to_encode, given_ids=given_ids
        )
        self.client.upload_points(
            collection_name=collection_name,
            points=vectorised_points,
        )

    def structure_points(
        self,
        points: list[dict],
        key_to_encode: str,
        given_ids: list[Any] = None,
    ):
        ids = (
            given_ids
            if given_ids and len(given_ids) == len(points)
            else [str(uuid.uuid4()) for _ in points]
        )
        payloads = self.get_payloads(points=points)
        structured_points = []
        for i, point in enumerate(points):
            vector_encoded_point = list(
                self.encoder.passage_embed(point[key_to_encode])
            )
            sparse_embeddings = list(
                self.sparse_encoder.passage_embed(point[key_to_encode])
            )
            updated_point = models.PointStruct(
                id=ids[i],
                vector={
                    "all-MiniLM-L6-v2": vector_encoded_point[0].tolist(),
                    "bm25": sparse_embeddings[0].as_object(),
                },
                payload=payloads[i],
            )
            structured_points.append(updated_point)
        return structured_points

    def retrieve_docs_based_on_query(
        self,
        collection_name: str,
        query: str,
        filter: Optional[dict[str:dict]] = None,
        limit: int = 3,
    ):
        dense_query_vector = next(self.encoder.query_embed(query))
        sparse_query_vector = next(self.sparse_encoder.query_embed(query))
        prefetch = [
            models.Prefetch(
                query=dense_query_vector,
                using="all-MiniLM-L6-v2",
                limit=limit,
            ),
            models.Prefetch(
                query=models.SparseVector(**sparse_query_vector.as_object()),
                using="bm25",
                limit=limit,
            ),
        ]
        if not filter:
            hits = self.client.query_points(
                collection_name=collection_name,
                prefetch=prefetch,
                query=models.FusionQuery(
                    fusion=models.Fusion.RRF,
                ),
                limit=limit,
            ).points
            return hits
        must_filter = self.create_filters(filter)
        hits = self.client.query_points(
            collection_name=collection_name,
            prefetch=prefetch,
            query=models.FusionQuery(
                fusion=models.Fusion.RRF,
            ),
            query_filter=models.Filter(must=must_filter),
            limit=limit,
            using="all-MiniLM-L6-v2",
        ).points
        return hits

    @staticmethod
    def get_payloads(points: list[dict]) -> list[dict]:
        return [{key: value for key, value in point.items()} for point in points]

    def create_payload_indexes(
        self, collection_name: str, index_fields: list[tuple[str, str]]
    ):
        """
        Create payload indexes for specified fields.

        """
        for field_name, field_type in index_fields:
            try:
                self.client.create_payload_index(
                    collection_name=collection_name,
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

    def encode_sparse(self, text: str):
        """
        Encode text into sparse vector using SentenceTransformers
        """
        sparse_embedding = self.sparse_encoder.encode([text])
        return sparse_embedding[0]

    def retrieve_docs_based_on_keyword_filters(
        self,
        collection_name: str,
        keyword_filters: dict[str:dict],
        limit: int = 3,
    ) -> str:
        filters = self.create_filters_by_must_should_keywords(keyword_filters)
        result = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=models.Filter(
                must=filters.get("must", []),
                should=filters.get("should", []),
            ),
            limit=limit,
        )
        interested_job_description = result[0][0].payload.get("description")
        return interested_job_description
