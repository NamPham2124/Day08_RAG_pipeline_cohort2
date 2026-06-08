# Ngày 8 — RAG Pipeline v2

**Chương 2 | Ngày 8 trong 15**

## Báo Cáo Hoàn Thành

### 1. Thông Tin Nhóm

| Thành viên | MSSV | Vai trò chính |
|---|---|---|
| Trần Đức Đăng Khôi | 2A202600889 | Technical Lead, tích hợp RAG, generation và demo |
| Lê Thiên Khang | 2A202600726 | Data Engineer, thu thập, chuẩn hóa và indexing |
| Nguyễn Thụy Như Quỳnh | 2A202600557 | Frontend/UX, chatbot, memory và hiển thị citation |
| Phạm Thành Nam | 2A202600832 | QA/Documentation, kiểm thử và kịch bản demo |

### 2. Phạm Vi Thực Hiện

- Hoàn thành pipeline cá nhân từ **Task 1 đến Task 10**.
- Sản phẩm nhóm được chọn: **DrugLaw RAG Chatbot** bằng Streamlit.
- Chatbot trả lời câu hỏi về pháp luật ma túy Việt Nam và tin tức liên quan.
- Tích hợp citation, conversation memory, source documents và retrieval score.
- Chạy local bằng Docker Desktop, Weaviate và Streamlit.

Evaluation pipeline bằng DeepEval/RAGAS/TruLens chưa được triển khai vì nhóm chọn sản
phẩm chatbot trong hai lựa chọn của đề bài. Tuy nhiên, bảng chấm điểm cuối README vẫn
dành 12 điểm cho Evaluation pipeline; cần triển khai thêm nếu giảng viên yêu cầu đồng
thời cả chatbot và evaluation.

### 3. Kết Quả Định Lượng

| Hạng mục | Kết quả hiện tại |
|---|---|
| Văn bản pháp luật | 7 PDF trong `data/landing/legal/` |
| Bài báo | 8 JSON trong `data/landing/news/` |
| Markdown chuẩn hóa | 15 file: 7 legal và 8 news |
| Chunking | 2.072 chunks |
| Embedding | `BAAI/bge-m3`, dimension 1024 |
| Vector store | Weaviate local qua Docker |
| Collection | `DrugLawDocs`, 2.072 objects |
| PageIndex Cloud | 3 PDF pháp luật đã upload, OCR và query |
| Automated tests | **38 passed** |
| Chatbot UI | Streamlit, chạy tại `http://localhost:8501` |

Các API key OpenAI, Jina và PageIndex đã được cấu hình trong `.env`. Giá trị thật không
được ghi vào README hoặc `.env.example`; `.env` đã được loại khỏi Git bằng `.gitignore`.

### 4. Kiến Trúc Hệ Thống

```text
PDF pháp luật + JSON bài báo
              |
              v
    Task 3: Markdown chuẩn hóa
              |
              v
 Task 4: Recursive chunking 500/50
              |
       +------+------+
       |             |
       v             v
 BGE-M3 dense     BM25 lexical
 + Weaviate         search
       |             |
       +------+------+
              v
        RRF + reranking
              |
     score thấp|score đạt
        v      v
   PageIndex   Top-k chunks
    fallback       |
                  v
       Reorder tránh lost-in-the-middle
                  |
                  v
       OpenAI/extractive generation
                  |
                  v
 Streamlit: answer + citation + sources
```

### 5. Báo Cáo Task Cá Nhân

| Task | Yêu cầu | Cách triển khai và kết quả |
|---|---|---|
| Task 1 | Thu thập tối thiểu 3 văn bản pháp luật | Có 7 PDF; hỗ trợ tải file an toàn, kiểm tra HTTP, extension và kích thước |
| Task 2 | Crawl tối thiểu 5 bài báo có metadata | Crawl4AI headless; có 8 JSON chứa URL, tiêu đề, ngày crawl và nội dung |
| Task 3 | Convert dữ liệu sang Markdown | MarkItDown; giữ cấu trúc `legal/` và `news/`; tạo 15 Markdown |
| Task 4 | Chunking và indexing | `RecursiveCharacterTextSplitter`, size `500`, overlap `50`; BGE-M3; Weaviate |
| Task 5 | Semantic search | Embed query bằng BGE-M3, tìm `near_vector`, trả kết quả theo score giảm dần |
| Task 6 | Lexical search | BM25Okapi, Unicode tokenization, lazy corpus/index loading |
| Task 7 | Reranking | RRF, MMR và Jina cross-encoder; có local fallback khi API lỗi |
| Task 8 | PageIndex vectorless RAG | Upload/query 3 PDF; parse retrieved nodes; structural local fallback |
| Task 9 | Retrieval pipeline | Semantic và lexical chạy song song, RRF merge, rerank, PageIndex fallback |
| Task 10 | Generation có citation | Top-k 5, reorder `[1,3,5,4,2]`, OpenAI generation và extractive fallback |

#### Task 1-3: Thu Thập Và Chuẩn Hóa

- File pháp luật gốc được lưu tại `data/landing/legal/`.
- Bài báo được lưu riêng từng file tại `data/landing/news/`.
- Task 2 dùng Crawl4AI và lưu URL lỗi để có thể chạy lại.
- Task 3 xử lý PDF/DOCX bằng MarkItDown và xử lý JSON bài báo bằng structured parser.
- Kết quả Markdown được lưu tại `data/standardized/legal/` và
  `data/standardized/news/`.

#### Task 4-6: Indexing Và Search

- Chọn recursive chunking vì dữ liệu gồm cả luật và bài báo, heading không đồng nhất.
- Overlap 50 ký tự giúp giữ ngữ cảnh qua biên chunk mà không tăng trùng lặp quá lớn.
- Chọn BGE-M3 vì hỗ trợ multilingual và phù hợp tiếng Việt.
- Embedding được normalize trước khi lưu vào Weaviate.
- Semantic search dùng cùng embedding model với lúc indexing.
- BM25 bổ sung khả năng tìm chính xác điều luật, tên riêng và từ khóa.

#### Task 7-9: Reranking Và Retrieval

- RRF hợp nhất danh sách dense và lexical mà không phụ thuộc thang điểm khác nhau.
- Jina reranker được dùng khi API sẵn sàng; lỗi API không làm pipeline dừng.
- Task 9 chạy semantic và lexical search song song bằng `ThreadPoolExecutor`.
- Nếu top result thấp hơn threshold `0.3`, pipeline chuyển sang PageIndex fallback.
- Mỗi module search được bọc lỗi riêng để chatbot vẫn hoạt động khi một dịch vụ lỗi.

#### Task 10: Generation Có Citation

- `TOP_K = 5`: đủ evidence nhưng không làm context quá dài.
- `TOP_P = 0.9`, `TEMPERATURE = 0.3`: ưu tiên factual answer, hạn chế suy đoán.
- Chunks được reorder để giảm hiệu ứng lost-in-the-middle.
- Prompt yêu cầu mọi factual claim phải có citation.
- Khi không đủ evidence, chatbot trả lời không thể xác minh thay vì đoán.
- Khi OpenAI không sẵn sàng, hệ thống dùng extractive fallback có citation.

### 6. Sản Phẩm Nhóm: DrugLaw RAG Chatbot

Entry point của sản phẩm nhóm là [`app.py`](app.py). Logic dùng chung được đặt tại
[`group_project/chatbot.py`](group_project/chatbot.py).

Các chức năng đã hoàn thành:

- Giao diện chat Streamlit.
- Sidebar cấu hình số nguồn và câu hỏi gợi ý.
- Trả lời có citation dựa trên Task 10.
- Conversation memory dùng các lượt chat gần nhất để hiểu follow-up question.
- Hiển thị tên nguồn, section, loại tài liệu, retrieval channel, score và excerpt.
- Nút xóa lịch sử hội thoại.
- Escape nội dung nguồn trước khi render HTML.
- Hiển thị lỗi có kiểm soát nếu Docker hoặc API chưa sẵn sàng.

Kịch bản demo:

1. Hỏi `Hình phạt cho tội tàng trữ trái phép chất ma túy là gì?`.
2. Mở phần nguồn tham khảo và kiểm tra citation.
3. Hỏi tiếp `Trường hợp đó có những khung hình phạt nào?` để kiểm tra memory.
4. Hỏi `Những nghệ sĩ nào từng liên quan đến ma túy?` để kiểm tra nguồn tin tức.

### 7. Cài Đặt Và Chạy

Tạo môi trường và cài dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Tạo `.env` từ `.env.example`, sau đó điền key thật:

```dotenv
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
JINA_API_KEY=...
PAGEINDEX_API_KEY=...
```

Khởi động Weaviate:

```powershell
docker compose up -d
docker compose ps
```

Rebuild dữ liệu và index khi cần:

```powershell
.\.venv\Scripts\python.exe src\task2_crawl_news.py
.\.venv\Scripts\python.exe src\task3_convert_markdown.py
.\.venv\Scripts\python.exe src\task4_chunking_indexing.py
```

Chạy chatbot:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Mở `http://localhost:8501`.

### 8. Kiểm Thử Và Xác Minh

Chạy toàn bộ test:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```

Kết quả gần nhất:

```text
38 passed
```

Kiểm tra số object trong Weaviate:

```powershell
.\.venv\Scripts\python.exe -c "import weaviate; c=weaviate.connect_to_local(); col=c.collections.use('DrugLawDocs'); print(col.aggregate.over_all(total_count=True).total_count); c.close()"
```

Kết quả đã xác minh: `2072`.

### 9. Hạn Chế Và Hướng Cải Tiến

- PageIndex free-trial không đủ quota để OCR toàn bộ PDF scan; hiện đã upload 3 PDF
  pháp luật cốt lõi.
- Jina, PageIndex và OpenAI là dịch vụ ngoài nên có thể timeout, hết quota hoặc bị thu
  hồi key; pipeline đã có fallback local.
- Chưa deploy chatbot public; demo hiện chạy local.
- Chưa triển khai Evaluation pipeline và golden dataset. Đây là phần nên bổ sung đầu
  tiên nếu yêu cầu chấm điểm bắt buộc cả chatbot lẫn evaluation.
- Có thể cải thiện bằng HyDE, citation validation, streaming answer và authentication.

### 10. Checklist Đối Chiếu

- [x] Task cá nhân 1-10 có implementation.
- [x] Dữ liệu legal và news đạt số lượng tối thiểu.
- [x] Chunking, BGE-M3 và Weaviate indexing hoạt động.
- [x] Semantic search, BM25, reranking và fallback hoạt động.
- [x] Generation có citation và không đoán khi thiếu evidence.
- [x] Chatbot Streamlit demo chạy local.
- [x] Conversation memory và source display.
- [x] README có kiến trúc, phân công, cách chạy và báo cáo.
- [x] Automated tests: 38 passed.
- [ ] Evaluation pipeline, golden dataset và báo cáo A/B.

---

## Mục Tiêu

Xây dựng một RAG pipeline thực tế, end-to-end, từ thu thập dữ liệu pháp luật và báo chí về ma tuý → xử lý → indexing → retrieval (hybrid + vectorless fallback) → generation có citation.

---

## Chủ Đề Dữ Liệu

**Pháp luật Việt Nam về ma tuý và các chất cấm** + **Các bài báo về nghệ sĩ liên quan tới ma tuý**

---

## Cấu Trúc Thư Mục

```
day_08_rag_pipeline_v2/
├── README.md
├── data/
│   ├── landing/          ← Task 1 & 2: raw files (PDF, DOCX, HTML)
│   └── standardized/     ← Task 3: converted markdown files
├── src/
│   ├── __init__.py
│   ├── task1_collect_legal_docs.py
│   ├── task2_crawl_news.py
│   ├── task3_convert_markdown.py
│   ├── task4_chunking_indexing.py
│   ├── task5_semantic_search.py
│   ├── task6_lexical_search.py
│   ├── task7_reranking.py
│   ├── task8_pageindex_vectorless.py
│   ├── task9_retrieval_pipeline.py
│   └── task10_generation.py
├── notebooks/
│   └── demo.ipynb         ← Notebook demo cho buổi trình bày
├── group_project/
│   └── README.md          ← Hướng dẫn bài tập nhóm
├── requirements.txt
└── .env.example
```

---

## Nhiệm Vụ Chi Tiết

### Task 1 — Thu Thập Văn Bản Pháp Luật (Cá nhân)

Tìm và tải về **tối thiểu 3 văn bản pháp luật** dạng PDF/DOCX về ma tuý và các chất cấm. Lưu vào `data/landing/`.

**Gợi ý nguồn:**
- Luật Phòng, chống ma tuý 2021 (Luật số 73/2021/QH15)
- Nghị định 105/2021/NĐ-CP hướng dẫn thi hành Luật Phòng chống ma tuý
- Bộ luật Hình sự 2015 (sửa đổi 2017) — Chương XX: Các tội phạm về ma tuý
- Thông tư liên tịch về danh mục chất ma tuý và tiền chất

**Yêu cầu:**
- Lưu file gốc (PDF/DOCX) vào `data/landing/legal/`
- Đặt tên file rõ ràng: `luat-phong-chong-ma-tuy-2021.pdf`, `nghi-dinh-105-2021.pdf`, ...

---

### Task 2 — Crawl Bài Báo (Cá nhân)

Crawl **tối thiểu 5 bài báo** về các nghệ sĩ Việt Nam liên quan tới ma tuý.

**Thư viện khuyến nghị:** [Crawl4AI](https://github.com/unclecode/crawl4ai)

**Yêu cầu:**
- Lưu output vào `data/landing/news/`
- Mỗi bài báo lưu thành 1 file (JSON hoặc HTML)
- Ghi rõ metadata: URL gốc, ngày crawl, tiêu đề bài báo

**Code mẫu (Crawl4AI):**
```python
from crawl4ai import AsyncWebCrawler

async def crawl_article(url: str, output_dir: str):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        # Lưu result.markdown vào file
        ...
```

---

### Task 3 — Convert Sang Markdown (Cá nhân)

Sử dụng [MarkItDown](https://github.com/microsoft/markitdown) của Microsoft để convert toàn bộ file trong `data/landing/` thành Markdown.

**Cài đặt:**
```bash
pip install markitdown
```

**Code mẫu:**
```python
from markitdown import MarkItDown

md = MarkItDown()

# Convert PDF
result = md.convert("data/landing/legal/luat-phong-chong-ma-tuy-2021.pdf")
print(result.text_content)

# Convert DOCX
result = md.convert("data/landing/legal/nghi-dinh-105-2021.docx")
```

**Yêu cầu:**
- Output lưu vào `data/standardized/`
- Giữ nguyên cấu trúc thư mục con (`legal/`, `news/`)
- Mỗi file output có tên tương ứng: `luat-phong-chong-ma-tuy-2021.md`

---

### Task 4 — Chunking & Indexing (Cá nhân)

Chọn **một loại chunking strategy** và **một embedding model** để index toàn bộ markdown files vào vector store.

**Chunking — khuyến khích dùng [langchain-text-splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/):**
```bash
pip install langchain-text-splitters
```

Các loại splitter phù hợp:
- `RecursiveCharacterTextSplitter` (mặc định, an toàn)
- `MarkdownHeaderTextSplitter` (tốt cho file có heading rõ)
- `SemanticChunker` (nâng cao, dùng embedding để tách)

**Embedding model gợi ý:**
- `sentence-transformers/all-MiniLM-L6-v2` (nhẹ, nhanh)
- `BAAI/bge-m3` (multilingual, tốt cho tiếng Việt)
- OpenAI `text-embedding-3-small` (nếu có API key)

**Vector Store — khuyến cáo dùng Weaviate:**
```bash
pip install weaviate-client
```
- Weaviate hỗ trợ hybrid search (dense + BM25) built-in
- Có thể dùng Docker hoặc Weaviate Cloud
- Alternatives: ChromaDB (đơn giản), FAISS (nếu chỉ cần dense)

**Yêu cầu:**
- Ghi rõ trong code: dùng chunking nào, chunk_size bao nhiêu, overlap bao nhiêu, vì sao
- Ghi rõ embedding model nào, dimension bao nhiêu
- Index thành công toàn bộ documents

---

### Task 5 — Semantic Search Module (Cá nhân)

Viết module thực hiện **semantic search** (dense retrieval) trên vector store.

**Yêu cầu:**
```python
def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
    """
    ...
```

- Input: query string + top_k
- Output: danh sách chunks có score, sorted descending
- Phải hoạt động được với embedding model đã chọn ở Task 4

---

### Task 6 — Lexical Search Module (Cá nhân)

Viết module thực hiện **lexical search**. Mặc định sử dụng **BM25**.

```bash
pip install rank-bm25
```

**Code mẫu BM25:**
```python
from rank_bm25 import BM25Okapi

# Tokenize corpus
tokenized_corpus = [doc.split() for doc in corpus]
bm25 = BM25Okapi(tokenized_corpus)

# Search
tokenized_query = query.split()
scores = bm25.get_scores(tokenized_query)
```

**Yêu cầu:**
```python
def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
    """
    ...
```

**Bonus:** Nếu dùng phương pháp khác (TF-IDF, Elasticsearch, Weaviate BM25 built-in), hãy giải thích cơ chế hoạt động trong buổi demo → **+5 điểm bonus**.

---

### Task 7 — Reranking Module (Cá nhân)

Viết module **reranking** để chấm lại độ liên quan của kết quả retrieval.

**Lựa chọn (chọn 1):**

| Phương pháp | Thư viện / Model | Đặc điểm |
|-------------|-----------------|-----------|
| Cross-encoder reranker | `jinaai/jina-reranker-v2-base-multilingual` | Multilingual, tốt cho tiếng Việt |
| Cross-encoder reranker | `Qwen/Qwen3-Reranker-0.6B` | Nhẹ, hiệu quả |
| MMR (Maximal Marginal Relevance) | Tự implement | Giảm trùng lặp, tăng diversity |
| RRF (Reciprocal Rank Fusion) | Tự implement | Gộp kết quả từ nhiều ranker |

**Code mẫu (Jina Reranker via API):**
```python
import requests

def rerank(query: str, documents: list[str], top_k: int = 5) -> list[dict]:
    response = requests.post(
        "https://api.jina.ai/v1/rerank",
        headers={"Authorization": "Bearer YOUR_API_KEY"},
        json={
            "model": "jina-reranker-v2-base-multilingual",
            "query": query,
            "documents": documents,
            "top_n": top_k
        }
    )
    return response.json()["results"]
```

**Yêu cầu:**
```python
def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Re-score and re-order candidates based on relevance to query.
    """
    ...
```

---

### Task 8 — PageIndex Vectorless RAG (Cá nhân)

Đăng ký tài khoản tại [https://pageindex.ai/](https://pageindex.ai/), sau đó sử dụng [PageIndex SDK](https://github.com/VectifyAI/PageIndex) để tạo một **vectorless RAG pipeline**.

**Cài đặt:**
```bash
pip install pageindex
```

**Tham khảo:** [https://github.com/VectifyAI/PageIndex](https://github.com/VectifyAI/PageIndex)

**Yêu cầu:**
- Upload tài liệu lên PageIndex
- Viết function query PageIndex và trả về kết quả
```python
def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval using PageIndex.
    Fallback khi hybrid search không trả về kết quả phù hợp.
    """
    ...
```

---

### Task 9 — Retrieval Pipeline Hoàn Chỉnh (Cá nhân)

Kết hợp tất cả modules thành một **retrieval pipeline** thống nhất với logic fallback:

```
Query
  │
  ├─→ Semantic Search (Task 5)  ──┐
  │                                ├─→ Merge + Rerank (Task 7) → Results
  ├─→ Lexical Search (Task 6)  ──┘
  │
  └─→ Nếu hybrid search không có kết quả đủ tốt (score < threshold)
        └─→ Fallback: PageIndex Vectorless (Task 8)
```

**Yêu cầu:**
```python
def retrieve(query: str, top_k: int = 5, score_threshold: float = 0.3) -> list[dict]:
    """
    1. Chạy semantic_search + lexical_search
    2. Merge kết quả (RRF hoặc weighted fusion)
    3. Rerank
    4. Nếu top result score < threshold → fallback PageIndex
    5. Return top_k results
    """
    ...
```

---

### Task 10 — Generation Có Citation (Cá nhân)

Sắp xếp lại context chunks sau reranking để **tránh lost in the middle**, inject vào prompt, và yêu cầu LLM trả lời có **citation**.

**Document Reordering (tránh lost in the middle):**
```python
def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks theo pattern: quan trọng nhất ở đầu và cuối,
    ít quan trọng hơn ở giữa.
    Ví dụ: [1, 3, 5, 4, 2] thay vì [1, 2, 3, 4, 5]
    """
    ...
```

**Prompt template:**
```python
SYSTEM_PROMPT = """Answer the following question comprehensively.
For every statement of fact or claim, immediately insert a citation
in brackets linking to the specific source
(e.g., [Author/Platform Name, Year]).
If the information is not explicitly stated in the provided context
or knowledge base, state 'I cannot verify this information'
rather than guessing."""

def generate_with_citation(query: str, context_chunks: list[dict]) -> str:
    """
    1. Reorder chunks để tránh lost in the middle
    2. Format context với source metadata
    3. Inject vào prompt với SYSTEM_PROMPT
    4. Gọi LLM (OpenAI, Gemini, hoặc local model)
    5. Return answer có citation
    """
    ...
```

**Yêu cầu:**
- Chọn top_k và top_p phù hợp (giải thích lý do trong code comment)
- Output phải có citation dạng `[Nguồn, Năm]`
- Nếu không đủ evidence → trả về "I cannot verify this information"

---

## Bài Tập Nhóm

> **Sau khi hoàn thành bài cá nhân**, ngồi lại với nhóm để xây dựng **1 trong 2 sản phẩm** sau:

---

### Yêu cầu 1: Sản phẩm nhóm RAG Chatbot

Xây dựng chatbot trả lời câu hỏi về pháp luật ma tuý và tin tức liên quan.

**Yêu cầu:**
- Giao diện chat (Streamlit / Gradio / Chainlit)
- Trả lời có citation (dựa trên Task 10)
- Hỗ trợ follow-up questions (conversation memory)
- Hiển thị source documents đã dùng

**Stack gợi ý:**
```
Chainlit/Streamlit → Retrieval (Task 9) → Generation (Task 10) → Display
```

---

### Yêu cầu 2: RAG Evaluation Pipeline

Sử dụng **1 trong 3 framework** sau để evaluate pipeline RAG của nhóm:

#### Framework lựa chọn

| Framework | Cài đặt | Đặc điểm |
|-----------|---------|-----------|
| [DeepEval](https://github.com/confident-ai/deepeval) | `pip install deepeval` | Nhiều metric built-in, dễ integrate với pytest |
| [RAGAS](https://github.com/explodinggradients/ragas) | `pip install ragas` | Chuẩn industry cho RAG eval, 3 trục chính |
| [TruLens](https://github.com/truera/trulens) | `pip install trulens` | Dashboard UI, feedback functions mạnh |

#### Yêu cầu Evaluation

1. **Tạo Golden Dataset** — tối thiểu 15 cặp Q&A (question, expected_answer, expected_context)
2. **Chạy evaluation** trên toàn bộ golden dataset với các metrics sau:
   - **Faithfulness** — câu trả lời có bám đúng context không?
   - **Answer Relevance** — câu trả lời có đúng câu hỏi không?
   - **Context Recall** — retriever có lấy đủ evidence không?
   - **Context Precision** — trong context lấy về, bao nhiêu % thực sự hữu ích?
3. **So sánh A/B** — chạy eval trên ít nhất 2 config khác nhau (ví dụ: có reranking vs không reranking, hoặc hybrid vs dense-only)
4. **Báo cáo** — bảng điểm + phân tích worst performers + đề xuất cải tiến

#### Code mẫu — DeepEval

```python
from deepeval import evaluate
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualRecallMetric,
    ContextualPrecisionMetric,
)
from deepeval.test_case import LLMTestCase

# Tạo test cases từ golden dataset
test_cases = []
for item in golden_dataset:
    result = rag_pipeline.generate_with_citation(item["question"])
    test_case = LLMTestCase(
        input=item["question"],
        actual_output=result["answer"],
        expected_output=item["expected_answer"],
        retrieval_context=[c["content"] for c in result["sources"]],
    )
    test_cases.append(test_case)

# Chạy evaluation
metrics = [
    FaithfulnessMetric(threshold=0.7),
    AnswerRelevancyMetric(threshold=0.7),
    ContextualRecallMetric(threshold=0.7),
    ContextualPrecisionMetric(threshold=0.7),
]

results = evaluate(test_cases, metrics)
```

#### Code mẫu — RAGAS

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from datasets import Dataset

# Chuẩn bị data
eval_data = {
    "question": [],
    "answer": [],
    "contexts": [],
    "ground_truth": [],
}

for item in golden_dataset:
    result = rag_pipeline.generate_with_citation(item["question"])
    eval_data["question"].append(item["question"])
    eval_data["answer"].append(result["answer"])
    eval_data["contexts"].append([c["content"] for c in result["sources"]])
    eval_data["ground_truth"].append(item["expected_answer"])

dataset = Dataset.from_dict(eval_data)

# Chạy evaluation
result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
)
print(result.to_pandas())
```

#### Code mẫu — TruLens

```python
from trulens.apps.custom import TruCustomApp, instrument
from trulens.core import Feedback
from trulens.providers.openai import OpenAI as TruOpenAI

provider = TruOpenAI()

# Define feedback functions
f_faithfulness = Feedback(provider.groundedness_measure_with_cot_reasons).on_output()
f_relevance = Feedback(provider.relevance).on_input_output()
f_context_relevance = Feedback(provider.context_relevance).on_input()

# Wrap RAG pipeline
tru_rag = TruCustomApp(
    rag_pipeline,
    app_name="DrugLaw_RAG",
    feedbacks=[f_faithfulness, f_relevance, f_context_relevance],
)

# Run evaluation
with tru_rag as recording:
    for item in golden_dataset:
        rag_pipeline.generate_with_citation(item["question"])

# View dashboard
from trulens.dashboard import run_dashboard
run_dashboard()
```

#### Deliverable Evaluation

- [ ] File `group_project/evaluation/golden_dataset.json` — 15+ cặp Q&A
- [ ] File `group_project/evaluation/eval_pipeline.py` — script chạy evaluation
- [ ] File `group_project/evaluation/results.md` — bảng điểm + phân tích
- [ ] So sánh A/B ít nhất 2 configs

---

### Yêu Cầu Chung

1. **Tích hợp pipeline** từ bài cá nhân của các thành viên
2. **Demo hoạt động được** trong buổi trình bày (chạy local hoặc deploy)
3. **Evaluation pipeline** chạy được và có báo cáo kết quả
4. **Code push lên repository** chung của nhóm
5. **README** mô tả kiến trúc và phân công (xem `group_project/README.md`)

---

### Kiến Trúc Hệ Thống

```
Streamlit UI
    |
    v
Conversation memory
    |
    v
Semantic Search (BGE-M3 + Weaviate) + BM25
    |
    v
RRF merge + Jina/local reranking
    |
    +-- score thấp --> PageIndex fallback
    |
    v
Task 10 generation có citation
    |
    v
Answer + source documents + retrieval score
```

---

### Phân Công Công Việc

| Thành viên | MSSV | Nhiệm vụ | Trạng thái |
|-----------|------|----------|------------|
| Trần Đức Đăng Khôi | 2A202600889 | Technical Lead, tích hợp RAG, generation và demo | Hoàn thành |
| Lê Thiên Khang | 2A202600726 | Thu thập, chuẩn hóa, chunking và indexing | Hoàn thành |
| Nguyễn Thụy Như Quỳnh | 2A202600557 | Streamlit UI, conversation memory và source display | Hoàn thành |
| Phạm Thành Nam | 2A202600832 | Kiểm thử, tài liệu và kịch bản demo | Hoàn thành |

---

### Hướng Dẫn Chạy

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy app
.\.venv\Scripts\python.exe -m streamlit run app.py
```

---

### Lưu ý

Hãy giữ lại repo này nếu như bạn học track 3 giai đoạn 2, chúng ta sẽ phát triển tiếp dự án lên knowledge graph để khắc phục các câu hỏi hóc búa khi có các câu hỏi khó.

---

## Cài Đặt Môi Trường

```bash
pip install -r requirements.txt
```

Tạo file `.env` từ `.env.example`:
```bash
cp .env.example .env
# Điền API keys vào .env
```

### Chạy Weaviate local và index BGE-M3

1. Mở Docker Desktop và chờ Docker Engine báo `Running`.
2. Khởi động Weaviate:

```bash
docker compose up -d
docker compose ps
```

3. Chạy pipeline indexing trong virtual environment:

```bash
.\.venv\Scripts\python.exe src\task4_chunking_indexing.py
```

Lần chạy đầu sẽ tải model `BAAI/bge-m3` từ Hugging Face. Model được cache
trên máy và các lần chạy sau sẽ dùng lại cache. Kiểm tra Weaviate tại
`http://localhost:8080/v1/.well-known/ready`.

Tắt Weaviate nhưng giữ dữ liệu:

```bash
docker compose down
```

---

## Chấm Điểm

### Tổng Quan Phân Bổ Điểm

| Thành phần | Tỷ trọng | Mô tả |
|-----------|----------|-------|
| **Bài Cá Nhân** | **50%** | 10 tasks, chấm bằng automated tests + manual review |
| **Bài Nhóm** | **30%** | RAG Chatbot + Evaluation pipeline |
| **Bonus** | **20%** | Các tiêu chí nâng cao (xem bên dưới) |

---

### Bài Cá Nhân — 50 điểm (50%)

Chấm bằng automated test suite (`pytest tests/ -v`). Mỗi task có test riêng.

| Task | Nội dung | Điểm | Test |
|------|----------|------|------|
| 1 | Thu thập văn bản pháp luật (≥3 files tồn tại trong `data/landing/legal/`) | 3 | `test_task1_*` |
| 2 | Crawl bài báo (≥5 files tồn tại trong `data/landing/news/`) | 3 | `test_task2_*` |
| 3 | Convert markdown (files tồn tại trong `data/standardized/`) | 4 | `test_task3_*` |
| 4 | Chunking + Indexing (vector store có data) | 7 | `test_task4_*` |
| 5 | Semantic search trả về kết quả đúng format, sorted | 6 | `test_task5_*` |
| 6 | Lexical search (BM25) trả về kết quả đúng format | 6 | `test_task6_*` |
| 7 | Reranking hoạt động, output re-sorted | 6 | `test_task7_*` |
| 8 | PageIndex query trả về kết quả | 4 | `test_task8_*` |
| 9 | Retrieval pipeline + fallback logic hoạt động | 7 | `test_task9_*` |
| 10 | Generation có citation + reorder | 4 | `test_task10_*` |
| **Tổng** | | **50** | |

---

### Bài Nhóm — 30 điểm (30%)

| Tiêu chí | Điểm |
|----------|------|
| RAG Chatbot demo hoạt động được | 8 |
| Tích hợp pipeline các thành viên | 4 |
| Kiến trúc rõ ràng + README | 3 |
| Chất lượng câu trả lời (có citation, đúng nội dung) | 3 |
| **Evaluation pipeline** (DeepEval / RAGAS / TruLens) | **12** |
| — Golden dataset ≥15 Q&A pairs | 3 |
| — Chạy eval với ≥4 metrics | 4 |
| — So sánh A/B ≥2 configs + phân tích | 3 |
| — Báo cáo kết quả có phân tích worst performers | 2 |

---

### Bonus — 20 điểm (20%)

| Tiêu chí | Điểm |
|----------|------|
| Giải thích cơ chế lexical search khác BM25 (trong demo) | 5 |
| Implement HyDE (Hypothetical Document Embeddings) cho query | 5 |
| Deploy chatbot online (Hugging Face Spaces / Render / ...) | 4 |
| Conversation memory (multi-turn chat) | 3 |
| UI/UX chất lượng (hiển thị source, score, highlight) | 3 |

---

### Chạy Test Chấm Điểm Bài Cá Nhân

```bash
# Chạy toàn bộ test suite
pytest tests/ -v

# Chạy từng task
pytest tests/test_individual.py::TestTask1 -v
pytest tests/test_individual.py::TestTask5 -v
```

---

## Hướng Dẫn Thời Gian

| Giai đoạn | Thời gian | Hoạt động |
|-----------|-----------|-----------|
| Task 1–3 | 0:00–0:45 | Thu thập data + convert markdown |
| Task 4–6 | 0:45–1:45 | Chunking, indexing, search modules |
| Task 7–8 | 1:45–2:15 | Reranking + PageIndex setup |
| Task 9–10 | 2:15–3:00 | Pipeline hoàn chỉnh + generation |
| Bài nhóm | Ngoài giờ | Tích hợp + build demo |

---

## Tài Liệu Tham Khảo

- [Crawl4AI](https://github.com/unclecode/crawl4ai) — Web crawling library
- [MarkItDown](https://github.com/microsoft/markitdown) — Microsoft document converter
- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/) — Chunking strategies
- [Weaviate](https://weaviate.io/developers/weaviate) — Vector database with hybrid search
- [rank-bm25](https://github.com/dorianbrown/rank_bm25) — BM25 implementation
- [PageIndex](https://github.com/VectifyAI/PageIndex) — Vectorless RAG
- [Jina Reranker](https://jina.ai/reranker/) — Cross-encoder reranking API
- Liu et al. (2023), *Lost in the Middle: How Language Models Use Long Contexts*
# Day08_RAG_pipeline_cohort2
