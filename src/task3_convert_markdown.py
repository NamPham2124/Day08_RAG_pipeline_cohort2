"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown.

Sử dụng MarkItDown của Microsoft:
    https://github.com/microsoft/markitdown

Cài đặt:
    pip install markitdown

Hướng dẫn:
    1. Scan toàn bộ file trong data/landing/ (PDF, DOCX, JSON)
    2. Convert sang Markdown
    3. Lưu vào data/standardized/ giữ nguyên cấu trúc thư mục
"""

import json
import sys
from pathlib import Path

from markitdown import MarkItDown

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    md = MarkItDown()

    for filepath in legal_dir.iterdir():
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Converting: {filepath.name}")
            result = md.convert(str(filepath))
            output_path = output_dir / f"{filepath.stem}.md"
            content = result.text_content.strip()
            if not content:
                content = (
                    f"# {filepath.stem}\n\n"
                    f"**Source file:** {filepath.name}\n\n"
                    "**Conversion status:** No embedded text layer was detected. "
                    "This document is likely a scanned PDF and requires OCR before "
                    "its full content can be indexed. The original source file is "
                    "preserved in `data/landing/legal/` for OCR processing.\n"
                )
                print(f"  [WARNING] No text layer detected: {filepath.name}")
            output_path.write_text(content, encoding="utf-8")
            print(f"  [SAVED] {output_path}")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filepath in news_dir.iterdir():
        if filepath.suffix.lower() == ".json":
            print(f"Converting: {filepath.name}")
            data = json.loads(filepath.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                print(f"  Skipped: {filepath.name} is not an article")
                continue

            output_path = output_dir / f"{filepath.stem}.md"
            header = (
                f"# {data.get('title', 'Unknown')}\n\n"
                f"**Source:** {data.get('url', 'N/A')}\n"
                f"**Crawled:** {data.get('date_crawled', 'N/A')}\n\n"
                "---\n\n"
            )
            content = header + data.get("content_markdown", data.get("content", ""))
            output_path.write_text(content, encoding="utf-8")
            print(f"  [SAVED] {output_path}")


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\n[DONE] Output tại:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()
