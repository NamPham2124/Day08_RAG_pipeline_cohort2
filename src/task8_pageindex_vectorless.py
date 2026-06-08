"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API
"""

import os
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
LANDING_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
MANIFEST_PATH = Path(__file__).parent.parent / "data" / "pageindex_documents.json"
DEFAULT_UPLOAD_FILES = [
    "Luat_73_2021.pdf",
    "Luat_ma_tuy_2021.pdf",
    "Nghi_dinh_2021.pdf",
]


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower(), flags=re.UNICODE))


def _build_structural_index() -> list[dict]:
    """Build a heading-based tree index without embeddings or a vector store."""
    nodes = []
    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        headings = []
        section_lines = []

        def add_section():
            section = "\n".join(section_lines).strip()
            if section:
                nodes.append({
                    "content": section,
                    "title": " > ".join(headings) or md_file.stem,
                    "metadata": {
                        "source": md_file.name,
                        "source_path": md_file.relative_to(STANDARDIZED_DIR).as_posix(),
                        "type": md_file.parent.name,
                    },
                })

        for line in content.splitlines():
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                add_section()
                level = len(heading_match.group(1))
                headings[level - 1:] = [heading_match.group(2).strip()]
                section_lines = [line]
            else:
                section_lines.append(line)
        add_section()
    return nodes


def _load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _save_manifest(manifest: dict):
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def upload_documents(filenames: list[str] | None = None) -> list[dict]:
    """
    Upload selected legal PDFs lên PageIndex Cloud và lưu doc_id vào manifest.

    Mặc định chỉ upload 3 tài liệu cốt lõi (171 trang) để nằm trong free-trial
    quota 200 active pages. Truyền filenames để chọn danh sách khác.
    """
    if not PAGEINDEX_API_KEY:
        raise ValueError("PAGEINDEX_API_KEY is not configured")

    from pageindex import PageIndexClient

    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    manifest = _load_manifest()
    remote_documents = client.list_documents(limit=100).get("documents", [])
    remote_by_name = {document.get("name"): document for document in remote_documents}
    uploaded = []

    for filename in filenames or DEFAULT_UPLOAD_FILES:
        filepath = LANDING_DIR / filename
        if not filepath.exists():
            print(f"  [WARNING] Missing file: {filepath}")
            continue

        remote = remote_by_name.get(filename)
        if remote:
            doc_id = remote.get("id")
            print(f"  [SKIP] Already uploaded: {filename} ({doc_id})")
        elif filename in manifest:
            doc_id = manifest[filename]["doc_id"]
            print(f"  [SKIP] Already in manifest: {filename} ({doc_id})")
        else:
            result = client.submit_document(str(filepath))
            doc_id = result["doc_id"]
            print(f"  [UPLOADED] {filename} ({doc_id})")

        manifest[filename] = {"doc_id": doc_id}
        uploaded.append({"filename": filename, "doc_id": doc_id})

    _save_manifest(manifest)
    return uploaded


def wait_for_documents(timeout: int = 900, interval: int = 15) -> dict:
    """Wait until uploaded PageIndex documents finish processing."""
    if not PAGEINDEX_API_KEY:
        raise ValueError("PAGEINDEX_API_KEY is not configured")

    from pageindex import PageIndexClient

    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    manifest = _load_manifest()
    deadline = time.monotonic() + timeout
    statuses = {}

    while time.monotonic() < deadline:
        statuses = {
            filename: client.get_document(item["doc_id"]).get("status", "unknown")
            for filename, item in manifest.items()
        }
        print("  Status:", statuses)
        if statuses and all(status == "completed" for status in statuses.values()):
            return statuses
        time.sleep(interval)

    return statuses


def sync_ocr_to_standardized() -> list[Path]:
    """Save completed PageIndex OCR results as standardized Markdown files."""
    if not PAGEINDEX_API_KEY:
        raise ValueError("PAGEINDEX_API_KEY is not configured")

    from pageindex import PageIndexClient

    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    manifest = _load_manifest()
    output_dir = STANDARDIZED_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    for filename, item in manifest.items():
        response = client.get_ocr(item["doc_id"], format="raw")
        content = response.get("result", "")
        if response.get("status") != "completed" or not isinstance(content, str) or not content.strip():
            print(f"  [WARNING] OCR is not ready: {filename}")
            continue

        output_path = output_dir / f"{Path(filename).stem}.md"
        output_path.write_text(content.strip(), encoding="utf-8")
        saved.append(output_path)
        print(f"  [SAVED OCR] {output_path}")
    return saved


def _flatten_relevant_contents(value):
    if isinstance(value, dict):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _flatten_relevant_contents(item)


def _cloud_search(query: str, top_k: int) -> list[dict]:
    import requests
    from pageindex import PageIndexClient

    def search_document(filename: str, doc_id: str) -> list[dict]:
        headers = {"api_key": PAGEINDEX_API_KEY}
        response = requests.post(
            f"{PageIndexClient.BASE_URL}/retrieval/",
            headers=headers,
            json={"doc_id": doc_id, "query": query, "thinking": False},
            timeout=30,
        )
        response.raise_for_status()
        retrieval_id = response.json()["retrieval_id"]

        retrieval = {}
        for _ in range(20):
            response = requests.get(
                f"{PageIndexClient.BASE_URL}/retrieval/{retrieval_id}/",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            retrieval = response.json()
            if retrieval.get("status") == "completed":
                break
            if retrieval.get("status") == "failed":
                retrieval = {}
                break
            time.sleep(2)

        document_results = []
        for node_rank, node in enumerate(retrieval.get("retrieved_nodes", []), 1):
            contents = _flatten_relevant_contents(node.get("relevant_contents", []))
            for content_rank, content in enumerate(contents, 1):
                physical_index = content.get("physical_index", "")
                page_match = re.search(r"\d+", physical_index)
                document_results.append({
                    "content": content.get("relevant_content", ""),
                    "score": 1.0 / (node_rank + content_rank - 1),
                    "metadata": {
                        "source": filename,
                        "type": "legal",
                        "section": content.get("section_title", node.get("title", "")),
                        "page_index": int(page_match.group()) if page_match else None,
                        "doc_id": doc_id,
                    },
                    "source": "pageindex",
                })
        return document_results

    results = []
    manifest = _load_manifest()
    with ThreadPoolExecutor(max_workers=min(3, len(manifest))) as executor:
        futures = {
            executor.submit(search_document, filename, item["doc_id"]): filename
            for filename, item in manifest.items()
        }
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as error:
                print(f"  [WARNING] PageIndex query failed for {futures[future]}: {error}")
    return sorted(results, key=lambda result: result["score"], reverse=True)[:top_k]


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    if not query.strip() or top_k <= 0:
        return []

    if PAGEINDEX_API_KEY and _load_manifest():
        try:
            cloud_results = _cloud_search(query, top_k)
            if cloud_results:
                return cloud_results
        except Exception as error:
            print(f"  [WARNING] PageIndex Cloud unavailable: {error}")

    query_tokens = _tokenize(query)
    scored = []
    for node in _build_structural_index():
        title_tokens = _tokenize(node["title"])
        content_tokens = _tokenize(node["content"])
        title_score = len(query_tokens & title_tokens) / max(len(query_tokens), 1)
        content_score = len(query_tokens & content_tokens) / max(len(query_tokens), 1)
        score = 0.6 * title_score + 0.4 * content_score
        if score > 0:
            scored.append({
                "content": node["content"],
                "score": float(score),
                "metadata": {**node["metadata"], "section": node["title"]},
                "source": "pageindex",
            })
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]


if __name__ == "__main__":
    print("Uploading selected documents to PageIndex Cloud...")
    upload_documents()
    wait_for_documents()
    sync_ocr_to_standardized()

    print("\nTest query:")
    results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
