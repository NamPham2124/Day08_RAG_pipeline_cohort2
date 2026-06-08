"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

import re

CORPUS: list[dict] = []  # List of {'content': str, 'metadata': dict}
_BM25 = None


def _tokenize(text: str) -> list[str]:
    """Tokenize Vietnamese text without requiring an additional NLP model."""
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def _ensure_index():
    global CORPUS, _BM25
    if _BM25 is None:
        from .task4_chunking_indexing import chunk_documents, load_documents

        CORPUS = chunk_documents(load_documents())
        _BM25 = build_bm25_index(CORPUS) if CORPUS else None
    return _BM25


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    from rank_bm25 import BM25Okapi

    if not corpus:
        raise ValueError("Cannot build a BM25 index from an empty corpus")
    return BM25Okapi([_tokenize(doc["content"]) for doc in corpus])


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    if not query.strip() or top_k <= 0:
        return []

    bm25 = _ensure_index()
    if bm25 is None:
        return []

    scores = bm25.get_scores(_tokenize(query))
    top_indices = sorted(
        range(len(scores)),
        key=lambda index: scores[index],
        reverse=True,
    )[:top_k]
    return [
        {
            "content": CORPUS[index]["content"],
            "score": float(scores[index]),
            "metadata": CORPUS[index]["metadata"],
        }
        for index in top_indices
        if scores[index] > 0
    ]


if __name__ == "__main__":
    # Test
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
