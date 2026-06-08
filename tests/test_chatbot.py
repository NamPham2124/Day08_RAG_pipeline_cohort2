"""Focused tests for group chatbot helpers and conversation memory."""

from group_project.chatbot import source_excerpt, source_label
from src.task10_generation import build_retrieval_query, format_conversation_history


def test_source_helpers():
    source = {
        "content": "Một   đoạn\ntrích tài liệu",
        "metadata": {"source": "luat.pdf", "section": "Điều 1"},
    }
    assert source_label(source, 1) == "luat.pdf - Điều 1"
    assert source_excerpt(source) == "Một đoạn trích tài liệu"


def test_follow_up_query_includes_recent_user_question():
    history = [
        {"role": "user", "content": "Tàng trữ ma túy bị xử lý thế nào?"},
        {"role": "assistant", "content": "Câu trả lời trước."},
    ]
    query = build_retrieval_query("Trường hợp đó có mức phạt nào?", history)
    assert "Tàng trữ ma túy" in query
    assert query.endswith("Trường hợp đó có mức phạt nào?")


def test_history_formatting_uses_roles():
    history = [
        {"role": "user", "content": "Câu hỏi"},
        {"role": "assistant", "content": "Câu trả lời"},
    ]
    formatted = format_conversation_history(history)
    assert "User: Câu hỏi" in formatted
    assert "Assistant: Câu trả lời" in formatted
