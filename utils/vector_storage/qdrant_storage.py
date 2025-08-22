from typing import Optional

from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer


class QdrantStorage:
    def __init__(
        self,
        collection_name: str,
        distance: str = models.Distance.COSINE,
        sentence_transformer_model: str = "all-MiniLM-L6-v2",
    ):
        self.client = QdrantClient(url="http://localhost:6333")
        self.collection_name = collection_name
        self.distance = distance
        self.encoder = SentenceTransformer(sentence_transformer_model)

    def create_collection(self):
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.encoder.get_sentence_embedding_dimension(),
                distance=models.Distance.COSINE,
            ),
        )

    def upload_points(
        self,
        points: list[dict],
        key_to_encode: str,
    ):
        """Upload points to Qdrant"""
        vectorised_points = self.structure_points(points=points, key_to_encode=key_to_encode)
        payloads = self.get_payloads(points=points, key_to_encode=key_to_encode)
        self.client.upsert(
            collection_name=self.collection_name,
            points = models.Batch(
                payloads = payloads,
                vectors= vectorised_points,
                ids = [i for i in range(len(vectorised_points))],
            )
        )

    def structure_points(
        self,
        points: list[dict],
        key_to_encode: str,
    ):
        """Vectorise points using encoder"""
        vectorised_points = []
        for point in points:
            vector = self.encoder.encode(point[key_to_encode]).tolist()
            vectorised_points.append(vector)
        return vectorised_points

    def encode_query(self, query: str):
        """Encode query using the same encoder"""
        encoded_query = self.encoder.encode(query).tolist()
        return encoded_query

    def retrieve_docs_based_on_query(
            self,
            query: str,
            filter:Optional[dict[str:dict]]=None,
            limit:int=3,):
        """Retrieve documents based on query"""
        encoded_query = self.encode_query(query)
        if not filter:
            hits = self.client.query_points(
                collection_name=self.collection_name,
                query=encoded_query,
                limit=limit,
            ).points
            return hits
        if filter:
            must_filter = self.create_filters(filter)
            hits = self.client.query_points(
            collection_name=self.collection_name,
            query=encoded_query,
            query_filter=models.Filter(
                must=must_filter
            ),
            limit=limit,
        ).points
            return hits
        return None

    @staticmethod
    def create_filters(filters:Optional[dict[str:dict]]):
        """Create filters for query"""
        filter_keys = filters.keys()
        if "must" in filter_keys:
            must_filters = []
            for key,value in filter_keys["must"].items():
                must_filter = models.FieldCondition(key=key, match=value)
                must_filters.append(must_filter)
            return must_filters
        return None

    @staticmethod
    def get_payloads(points: list[dict], key_to_encode: str) -> list[dict]:
        """For simplicity lets assume,
        payload is everything except the key_to_encode which has the long decsription"""
        payload_list = []
        for point in points:
            point_payload_data = {
                key: value for key, value in point.items() if key != key_to_encode
            }
            payload_list.append(point_payload_data)
        return payload_list

