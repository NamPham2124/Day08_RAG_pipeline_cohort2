"""Shared helpers for the Streamlit RAG chatbot."""

from src.task10_generation import generate_with_citation


SUGGESTED_QUESTIONS = [
    "Hình phạt cho tội tàng trữ trái phép chất ma túy là gì?",
    "Cai nghiện ma túy tự nguyện được thực hiện ở đâu?",
    "Những nghệ sĩ nào từng liên quan đến ma túy?",
]


def answer_question(
    question: str,
    conversation_history: list[dict] | None = None,
    top_k: int = 5,
) -> dict:
    """Generate a cited answer using recent conversation turns as memory."""
    return generate_with_citation(
        question,
        top_k=top_k,
        conversation_history=conversation_history,
    )


def source_label(source: dict, index: int) -> str:
    metadata = source.get("metadata", {})
    filename = metadata.get("source", f"Nguồn {index}")
    section = metadata.get("section")
    return f"{filename} - {section}" if section else filename


def source_excerpt(source: dict, max_length: int = 450) -> str:
    content = " ".join(source.get("content", "").split())
    if len(content) <= max_length:
        return content
    return content[:max_length].rsplit(" ", 1)[0] + "..."
