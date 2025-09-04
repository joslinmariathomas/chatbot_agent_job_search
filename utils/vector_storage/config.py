QdrantClientServer = "http://qdrant:6333"
FILTER_CONDITIONS_BY_KEYS = {
    "must": ["url"],
    "should": [
        "job_position",
        "suburb",
        "company_name",
    ],
}
