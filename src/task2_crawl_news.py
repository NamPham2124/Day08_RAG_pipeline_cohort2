"""
Task 2 — Crawl bài báo về nghệ sĩ liên quan tới ma tuý.

Yêu cầu:
    1. Crawl tối thiểu 5 bài báo từ các trang tin tức Việt Nam.
    2. Sử dụng Crawl4AI hoặc thư viện crawling tương tự.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata:
       url, title, date_crawled, content.

Cài đặt:
    pip install -U crawl4ai
    crawl4ai-setup
    crawl4ai-doctor
"""

import asyncio
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


# Nếu file này nằm trong src/ hoặc scripts/ thì parent.parent sẽ trỏ về project root.
# Nếu file này nằm ngay project root, đổi thành: Path("data/landing/news")
DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# Danh sách URL mẫu. Nên để >5 URL phòng trường hợp một số trang chặn crawler.
ARTICLE_URLS = [
    "https://tuoitre.vn/bat-ca-si-long-nhat-va-ca-si-son-ngoc-minh-vi-lien-quan-ma-tuy-20260520082138943.htm",
    "https://tuoitre.vn/ca-si-long-nhat-khai-su-dung-ma-tuy-da-cung-quan-ly-20260520132251413.htm",
    "https://tuoitre.vn/ca-si-long-nhat-thua-nhan-da-nhieu-lan-dat-mua-ma-tuy-ve-su-dung-20260520161117184.htm",
    "https://dantri.com.vn/van-hoa/nhung-nghe-si-viet-lao-dao-vi-dinh-vao-ma-tuy-20230424033137629.htm",
    "https://dantri.com.vn/phap-luat/truoc-ca-si-chu-bin-loat-nghe-si-noi-tieng-vuong-lao-ly-vi-ma-tuy-20240608123002810.htm",
    "https://tienphong.vn/nhieu-nghe-si-viet-bi-bat-vi-dinh-vao-ma-tuy-post1649760.tpo",
    "https://tienphong.vn/nghe-si-dinh-ma-tuy-khoang-trong-sau-nhung-cu-truot-nga-post1845503.tpo",
    "https://tuoitre.vn/khoi-to-3-bi-can-trong-vu-ca-si-miu-le-su-dung-ma-tuy-o-cat-ba-20260514230349573.htm",
]


def slugify(text: str, max_len: int = 80) -> str:
    """Chuyển title thành tên file an toàn."""
    text = text or "unknown"

    # Bỏ dấu tiếng Việt
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Chỉ giữ chữ, số, gạch ngang
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")

    return text[:max_len] or "unknown"


def get_markdown(result) -> str:
    """
    Crawl4AI có phiên bản trả result.markdown là str,
    có phiên bản trả object có raw_markdown / fit_markdown.
    Hàm này xử lý cả hai.
    """
    markdown = getattr(result, "markdown", None)

    if markdown is None:
        return ""

    if isinstance(markdown, str):
        return markdown.strip()

    fit_markdown = getattr(markdown, "fit_markdown", None)
    raw_markdown = getattr(markdown, "raw_markdown", None)

    return (fit_markdown or raw_markdown or str(markdown)).strip()


def extract_title(result, content: str) -> str:
    """Lấy title từ metadata, nếu không có thì lấy heading đầu tiên trong markdown."""
    metadata = getattr(result, "metadata", None) or {}

    title = (
        metadata.get("title")
        or metadata.get("og:title")
        or metadata.get("twitter:title")
    )

    if title:
        return title.strip()

    # Fallback: lấy heading đầu tiên từ markdown
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return re.sub(r"^#+\s*", "", line).strip()

    return "Unknown"


async def crawl_article(crawler: AsyncWebCrawler, url: str) -> dict:
    """
    Crawl một bài báo và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str,
            "content": str,
            "content_markdown": str,
            "status_code": int | None
        }
    """
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=60000,
    )

    result = await crawler.arun(url=url, config=run_config)

    if not result.success:
        raise RuntimeError(
            f"Crawl failed: {url} | "
            f"status={getattr(result, 'status_code', None)} | "
            f"error={getattr(result, 'error_message', None)}"
        )

    content = get_markdown(result)
    title = extract_title(result, content)

    # Check nhẹ để tránh lưu trang lỗi / trang rỗng
    if len(content) < 200:
        raise RuntimeError(f"Content too short, maybe blocked or empty: {url}")

    return {
        "url": url,
        "final_url": getattr(result, "url", url),
        "title": title,
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "content": content,
        "content_markdown": content,
        "status_code": getattr(result, "status_code", None),
    }


async def crawl_all():
    """Crawl toàn bộ bài báo trong ARTICLE_URLS."""
    setup_directory()

    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
    )

    saved_count = 0
    failed_urls = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for i, url in enumerate(ARTICLE_URLS, 1):
            print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")

            try:
                article = await crawl_article(crawler, url)
            except Exception as e:
                print(f"  [FAILED] {e}")
                failed_urls.append({"url": url, "error": str(e)})
                continue

            saved_count += 1

            title_slug = slugify(article["title"])
            url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
            filename = f"article_{saved_count:02d}_{title_slug}_{url_hash}.json"

            filepath = DATA_DIR / filename
            filepath.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            print(f"  [SAVED] {filepath}")

            # Nghỉ nhẹ để không spam server báo
            await asyncio.sleep(1)

    # Lưu log các URL bị lỗi nếu có
    if failed_urls:
        error_path = DATA_DIR / "_failed_urls.json"
        error_path.write_text(
            json.dumps(failed_urls, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n[WARNING] Có {len(failed_urls)} URL lỗi. Xem log: {error_path}")

    print(f"\nDone. Saved {saved_count} article(s) to: {DATA_DIR}")

    if saved_count < 5:
        print("[WARNING] Chưa đủ 5 bài. Hãy bổ sung thêm URL hoặc thay URL bị chặn.")


if __name__ == "__main__":
    if not ARTICLE_URLS:
        print("[WARNING] Hãy điền ARTICLE_URLS trước khi chạy!")
    else:
        asyncio.run(crawl_all())
