"""
Task 10 — Generation Có Citation.

Hướng dẫn:
    1. Chọn top_k, top_p phù hợp (giải thích lý do)
    2. Sắp xếp lại chunks sau reranking để tránh "lost in the middle"
    3. Inject context vào prompt
    4. Yêu cầu LLM trả lời có citation
    5. Nếu không đủ evidence → "I cannot verify this information"
"""

import os
from dotenv import load_dotenv

load_dotenv()

from .task9_retrieval_pipeline import retrieve


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn
# =============================================================================

# top_k: Số chunks đưa vào context
# Chọn 5 vì: đủ evidence mà không quá dài gây lost in the middle
TOP_K = 5

# top_p (nucleus sampling): Xác suất tích luỹ cho token generation
# Chọn 0.9 vì: đủ diverse nhưng không quá random
TOP_P = 0.9

# temperature: Độ ngẫu nhiên của output
# Chọn 0.3 vì: RAG cần factual, ít sáng tạo
TEMPERATURE = 0.3
MAX_HISTORY_MESSAGES = 6


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """Answer the following question comprehensively in Vietnamese.
For every statement of fact or claim, immediately insert a citation in brackets
linking to the specific source (e.g., [Luật Phòng chống ma tuý 2021, Điều 3]
or [VnExpress, 2024]).

If the information is not explicitly stated in the provided context or knowledge
base, state 'Tôi không thể xác minh thông tin này từ nguồn hiện có' rather than
guessing.

Rules:
- Only use information from the provided context
- Every factual claim MUST have a citation
- If context is insufficient, say so clearly
- Structure your answer with clear paragraphs"""


# =============================================================================
# DOCUMENT REORDERING (tránh lost in the middle)
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks để tránh "lost in the middle" effect.

    LLM nhớ tốt thông tin ở ĐẦU và CUỐI prompt, quên thông tin ở GIỮA.
    Strategy: đặt chunks quan trọng nhất ở đầu và cuối, kém quan trọng ở giữa.

    Input order (by score):  [1, 2, 3, 4, 5]
    Output order:            [1, 3, 5, 4, 2]
    (best first, worst in middle, second-best last)

    Args:
        chunks: List sorted by score descending (from retrieval)

    Returns:
        List reordered để maximize LLM attention.
    """
    if len(chunks) <= 2:
        return list(chunks)
    return list(chunks[::2]) + list(reversed(chunks[1::2]))


# =============================================================================
# CONTEXT FORMATTING
# =============================================================================

def format_context(chunks: list[dict]) -> str:
    """
    Format chunks thành context string cho prompt.
    Mỗi chunk có label source để LLM có thể cite.

    Args:
        chunks: List of {'content': str, 'metadata': dict, 'score': float}

    Returns:
        Formatted context string.
    """
    context_parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", f"Source {index}")
        doc_type = metadata.get("type", "unknown")
        section = metadata.get("section", "")
        label = f"Document {index} | Source: {source} | Type: {doc_type}"
        if section:
            label += f" | Section: {section}"
        context_parts.append(f"[{label}]\n{chunk['content'].strip()}")
    return "\n\n---\n\n".join(context_parts)


def _extractive_fallback(chunks: list[dict]) -> str:
    """Return a cited answer when no LLM API key is configured."""
    if not chunks:
        return "Tôi không thể xác minh thông tin này từ nguồn hiện có."

    statements = []
    for chunk in chunks[:3]:
        source = chunk.get("metadata", {}).get("source", "Nguồn không xác định")
        content = " ".join(chunk["content"].split())
        excerpt = content[:350].rsplit(" ", 1)[0]
        if excerpt:
            statements.append(f"{excerpt}. [{source}]")
    return "\n\n".join(statements) or "Tôi không thể xác minh thông tin này từ nguồn hiện có."


def build_retrieval_query(query: str, conversation_history: list[dict] | None = None) -> str:
    """Add recent user turns so follow-up questions remain retrievable."""
    if not conversation_history:
        return query

    previous_questions = [
        message["content"]
        for message in conversation_history[-MAX_HISTORY_MESSAGES:]
        if message.get("role") == "user" and message.get("content")
    ]
    if not previous_questions:
        return query
    return "\n".join([*previous_questions[-2:], query])


def format_conversation_history(conversation_history: list[dict] | None = None) -> str:
    """Format recent chat turns for the generation prompt."""
    if not conversation_history:
        return "No previous conversation."

    parts = []
    for message in conversation_history[-MAX_HISTORY_MESSAGES:]:
        role = "User" if message.get("role") == "user" else "Assistant"
        content = message.get("content", "").strip()
        if content:
            parts.append(f"{role}: {content}")
    return "\n".join(parts) or "No previous conversation."


# =============================================================================
# GENERATION
# =============================================================================

def generate_with_citation(
    query: str,
    top_k: int = TOP_K,
    conversation_history: list[dict] | None = None,
) -> dict:
    """
    End-to-end RAG generation có citation.

    Pipeline:
        1. Retrieve relevant chunks
        2. Reorder để tránh lost in the middle
        3. Format context với source labels
        4. Build prompt (system + context + query)
        5. Call LLM
        6. Return answer + sources

    Args:
        query: Câu hỏi của user

    Returns:
        {
            'answer': str,           # Câu trả lời có citation
            'sources': list[dict],   # Các chunks đã dùng
            'retrieval_source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    retrieval_query = build_retrieval_query(query, conversation_history)
    chunks = retrieve(retrieval_query, top_k=top_k)
    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    history = format_conversation_history(conversation_history)
    api_key = os.getenv("OPENAI_API_KEY", "")

    if api_key and chunks:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Conversation history:\n{history}\n\n---\n\n"
                        f"Context:\n{context}\n\n---\n\n"
                        f"Current question: {query}"
                    ),
                },
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        answer = response.choices[0].message.content
    else:
        answer = _extractive_fallback(reordered)

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0].get("source", "hybrid") if chunks else "none",
        "retrieval_query": retrieval_query,
    }


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo pháp luật Việt Nam?",
        "Những nghệ sĩ nào đã bị bắt vì liên quan tới ma tuý?",
        "Quy trình cai nghiện bắt buộc theo Luật Phòng chống ma tuý 2021?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
