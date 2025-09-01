import json
import uuid

from utils.vector_storage.qdrant_storage import QdrantStorage


def test_create_collection():
    collection_name = f"test_collection_{uuid.uuid4()}"
    qdrant_storage = QdrantStorage(
        collection_name=collection_name, client_server="http://localhost:6333"
    )
    assert not qdrant_storage.client.collection_exists(collection_name=collection_name)
    qdrant_storage.create_collection()
    assert qdrant_storage.client.collection_exists(collection_name=collection_name)
    qdrant_storage.client.delete_collection(collection_name=collection_name)


def test_upload_points():
    with open("./test_documents.json", "r") as file:
        data = json.load(file)
    collection_name = f"test_collection_{uuid.uuid4()}"
    qdrant_storage = QdrantStorage(
        collection_name=collection_name, client_server="http://localhost:6333"
    )
    assert not qdrant_storage.client.collection_exists(collection_name=collection_name)
    qdrant_storage.create_collection()
    qdrant_storage.upload_points(points=data, key_to_encode="description")
    points_count = qdrant_storage.client.count(collection_name=collection_name)
    assert points_count.count == len(data)
    qdrant_storage.client.delete_collection(collection_name=collection_name)


def test_retrieve_docs_based_on_query():
    with open("./test_documents.json", "r") as file:
        data = json.load(file)
    collection_name = f"test_collection_{uuid.uuid4()}"
    qdrant_storage = QdrantStorage(
        collection_name=collection_name, client_server="http://localhost:6333"
    )
    qdrant_storage.create_collection()
    qdrant_storage.upload_points(points=data, key_to_encode="description")
    query = "alien invasion"
    limit = 3
    retrieved_points = qdrant_storage.retrieve_docs_based_on_query(
        query=query, limit=limit
    )
    assert len(retrieved_points) == limit
    payload_keys = ["name", "year", "author"]
    assert set(retrieved_points[0].payload.keys()) == set(payload_keys)
    assert retrieved_points[0].payload["name"] == "The War of the Worlds"
    qdrant_storage.client.delete_collection(collection_name=collection_name)
