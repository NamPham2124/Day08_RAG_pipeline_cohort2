# Bài tập nhóm: DrugLaw RAG Chatbot

Nhóm chọn xây dựng **RAG Chatbot** trả lời câu hỏi về pháp luật ma túy Việt Nam
và tin tức liên quan. Sản phẩm tích hợp toàn bộ pipeline từ Task 1 đến Task 10.

## Tính năng đã hoàn thành

- Giao diện chat bằng Streamlit.
- Trả lời bằng dữ liệu đã thu thập, có citation.
- Conversation memory: dùng các lượt hỏi gần nhất để xử lý câu hỏi follow-up.
- Hiển thị tài liệu nguồn, loại tài liệu, kênh retrieval, score và đoạn trích.
- Hybrid retrieval: BGE-M3 semantic search + BM25 + RRF/reranking.
- PageIndex vectorless fallback khi kết quả hybrid không đủ tốt.
- Có chế độ trả lời extractive fallback khi không cấu hình OpenAI API key.

## Kiến trúc

```text
Người dùng
    |
    v
Streamlit UI (app.py)
    |
    v
Conversation memory + retrieval query expansion
    |
    v
Task 9 Retrieval Pipeline
    |------------------------------|
    v                              v
BGE-M3 + Weaviate             BM25 lexical search
    |------------------------------|
                    |
                    v
             RRF + reranking
                    |
        score thấp  |  score đạt yêu cầu
           v        v
     PageIndex      Top-k chunks
       fallback          |
                        v
            Task 10 reorder + generation
                        |
                        v
            Answer + citation + sources
```

## Phân công

| Thành viên | MSSV | Vai trò và nhiệm vụ | Trạng thái |
|---|---|---|---|
| Trần Đức Đăng Khôi | 2A202600889 | Technical Lead; tích hợp RAG, generation, cấu hình và demo | Hoàn thành |
| Lê Thiên Khang | 2A202600726 | Data Engineer; thu thập, chuẩn hóa, chunking và indexing | Hoàn thành |
| Nguyễn Thụy Như Quỳnh | 2A202600557 | Frontend/UX; Streamlit UI, conversation memory, citation và source display | Hoàn thành |
| Phạm Thành Nam | 2A202600832 | QA/Documentation; kiểm thử, kịch bản demo, README và release checklist | Hoàn thành |

Phân công trên thể hiện trách nhiệm báo cáo và trình bày. Code hiện được tích hợp trong
một repository chung để cả nhóm có thể chạy và kiểm thử cùng một phiên bản.

## Cấu hình

1. Cài Python dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. Tạo `.env` từ `.env.example` và điền các key cần dùng:

```dotenv
OPENAI_API_KEY=...
JINA_API_KEY=...
PAGEINDEX_API_KEY=...
```

`OPENAI_API_KEY` dùng để sinh câu trả lời tự nhiên. Khi thiếu key, chatbot vẫn trả lời
bằng đoạn trích có citation. Jina và PageIndex cũng có local fallback khi API không sẵn sàng.

3. Mở Docker Desktop và khởi động Weaviate:

```powershell
docker compose up -d
docker compose ps
```

4. Nếu collection chưa có dữ liệu, chạy indexing:

```powershell
.\.venv\Scripts\python.exe src\task4_chunking_indexing.py
```

## Chạy chatbot

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Mở `http://localhost:8501`, nhập câu hỏi hoặc chọn câu hỏi gợi ý ở sidebar.

## Kịch bản demo

1. Hỏi: `Hình phạt cho tội tàng trữ trái phép chất ma túy là gì?`
2. Kiểm tra answer có citation và mở phần nguồn tham khảo.
3. Hỏi follow-up: `Trường hợp đó có những khung hình phạt nào?`
4. Quan sát chatbot dùng lịch sử hội thoại để truy xuất đúng chủ đề.
5. Hỏi về nghệ sĩ liên quan đến ma túy để minh họa retrieval trên nguồn tin tức.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```

## Phạm vi lựa chọn

Nhóm chọn sản phẩm **RAG Chatbot** trong hai lựa chọn của đề bài. Evaluation pipeline
không phải sản phẩm được chọn, vì vậy các deliverable DeepEval/RAGAS/TruLens không nằm
trong phạm vi triển khai này.
