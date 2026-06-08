"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""

from functools import lru_cache

from .task4_chunking_indexing import COLLECTION_NAME, EMBEDDING_MODEL


@lru_cache(maxsize=1)
def _get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    if not query.strip() or top_k <= 0:
        return []

    try:
        import weaviate
        from weaviate.classes.query import MetadataQuery
    except ImportError:
        return []

    try:
        with weaviate.connect_to_local() as client:
            if not client.collections.exists(COLLECTION_NAME):
                return []

            query_embedding = _get_embedding_model().encode(
                query,
                normalize_embeddings=True,
            ).tolist()
            collection = client.collections.use(COLLECTION_NAME)
            response = collection.query.near_vector(
                near_vector=query_embedding,
                limit=top_k,
                return_metadata=MetadataQuery(distance=True),
            )
    except Exception as error:
        print(f"  [WARNING] Semantic search unavailable: {error}")
        return []

    results = []
    for obj in response.objects:
        properties = obj.properties
        distance = obj.metadata.distance
        results.append({
            "content": properties["content"],
            "score": float(1 - distance) if distance is not None else 0.0,
            "metadata": {
                "source": properties.get("source", "unknown"),
                "source_path": properties.get("source_path", ""),
                "type": properties.get("doc_type", "unknown"),
                "chunk_index": properties.get("chunk_index", 0),
            },
        })
    return sorted(results, key=lambda item: item["score"], reverse=True)


if __name__ == "__main__":
    # Test
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
