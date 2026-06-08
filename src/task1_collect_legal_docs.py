"""
Task 1 — Thu thập văn bản pháp luật về ma tuý và các chất cấm.

Hướng dẫn:
    1. Tìm tối thiểu 3 văn bản pháp luật (PDF/DOCX) từ các nguồn chính thống.
    2. Tải về và lưu vào data/landing/legal/
    3. Đặt tên file rõ ràng, không dấu, có năm ban hành.

Gợi ý nguồn:
    - https://thuvienphapluat.vn
    - https://vanban.chinhphu.vn
    - https://luatvietnam.vn

Gợi ý văn bản:
    - Luật Phòng, chống ma tuý 2021 (73/2021/QH15)
    - Nghị định 105/2021/NĐ-CP
    - Bộ luật Hình sự 2015 (sửa đổi 2017) - Chương XX
    - Nghị định 57/2022/NĐ-CP về danh mục chất ma tuý
"""

from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
VALID_EXTENSIONS = {".pdf", ".doc", ".docx"}


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Thư mục đã sẵn sàng: {DATA_DIR}")


def download_file(url: str, filename: str) -> Path:
    """Tải một văn bản pháp luật từ direct URL vào landing/legal."""
    output_path = DATA_DIR / Path(filename).name
    if output_path.suffix.lower() not in VALID_EXTENSIONS:
        raise ValueError(f"Unsupported legal document type: {output_path.suffix}")

    setup_directory()
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    if len(response.content) < 1024:
        raise ValueError(f"Downloaded file is unexpectedly small: {url}")

    temporary_path = output_path.with_suffix(output_path.suffix + ".part")
    temporary_path.write_bytes(response.content)
    temporary_path.replace(output_path)
    print(f"[OK] Đã tải: {output_path}")
    return output_path


def download_documents(documents: list[dict[str, str]]) -> list[Path]:
    """Tải danh sách {'url': ..., 'filename': ...} và trả về các path đã lưu."""
    return [
        download_file(document["url"], document["filename"])
        for document in documents
    ]


if __name__ == "__main__":
    setup_directory()
