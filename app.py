"""Streamlit interface for the Vietnamese drug-law RAG chatbot."""

from html import escape

import streamlit as st

from group_project.chatbot import (
    SUGGESTED_QUESTIONS,
    answer_question,
    source_excerpt,
    source_label,
)


st.set_page_config(
    page_title="DrugLaw RAG Assistant",
    page_icon="⚖️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1100px; padding-top: 2rem;}
    .source-card {
        border: 1px solid #d9e2ec;
        border-radius: 10px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.7rem;
        background: #f8fafc;
    }
    .source-title {font-weight: 700; color: #102a43;}
    .source-meta {font-size: 0.85rem; color: #627d98; margin-bottom: 0.35rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def render_sources(sources: list[dict]):
    if not sources:
        st.info("Không có tài liệu nguồn phù hợp.")
        return

    for index, source in enumerate(sources, 1):
        metadata = source.get("metadata", {})
        score = float(source.get("score", 0.0))
        retrieval_source = escape(str(source.get("source", "hybrid")))
        doc_type = escape(str(metadata.get("type", "unknown")))
        label = escape(source_label(source, index))
        excerpt = escape(source_excerpt(source))
        st.markdown(
            (
                '<div class="source-card">'
                f'<div class="source-title">{index}. {label}</div>'
                f'<div class="source-meta">Loại: {doc_type} · '
                f'Kênh: {retrieval_source} · Score: {score:.3f}</div>'
                f"<div>{excerpt}</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )


def initialize_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None


initialize_state()

with st.sidebar:
    st.header("Cấu hình")
    top_k = st.slider("Số nguồn sử dụng", min_value=3, max_value=8, value=5)
    st.caption("Pipeline: BGE-M3 + Weaviate + BM25 + RRF + PageIndex fallback")
    st.success("Trả lời có citation và hiển thị nguồn")

    if st.button("Xóa hội thoại", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_question = None
        st.rerun()

    st.divider()
    st.subheader("Câu hỏi gợi ý")
    for question in SUGGESTED_QUESTIONS:
        if st.button(question, use_container_width=True):
            st.session_state.pending_question = question

st.title("DrugLaw RAG Assistant")
st.write(
    "Trợ lý hỏi đáp về pháp luật ma túy Việt Nam và tin tức liên quan. "
    "Mỗi câu trả lời sử dụng dữ liệu đã thu thập và kèm nguồn tham khảo."
)

if not st.session_state.messages:
    st.info(
        "Hãy đặt câu hỏi đầu tiên hoặc chọn một câu hỏi gợi ý. "
        "Bạn có thể hỏi tiếp bằng các đại từ như “quy định đó” hoặc “trường hợp này”."
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander(f"Nguồn tham khảo ({len(message['sources'])})"):
                render_sources(message["sources"])

question = st.chat_input("Nhập câu hỏi về pháp luật hoặc tin tức ma túy...")
if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None

if question:
    history = [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state.messages
    ]
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm tài liệu và tạo câu trả lời..."):
            try:
                result = answer_question(question, history, top_k=top_k)
                answer = result["answer"]
                sources = result.get("sources", [])
                st.markdown(answer)
                with st.expander(f"Nguồn tham khảo ({len(sources)})", expanded=True):
                    render_sources(sources)
            except Exception as error:
                answer = (
                    "Không thể xử lý câu hỏi lúc này. Hãy kiểm tra Docker/Weaviate "
                    f"và API key. Chi tiết: `{error}`"
                )
                sources = []
                st.error(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )
