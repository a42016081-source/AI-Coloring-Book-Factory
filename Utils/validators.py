"""Input validators."""
from typing import Any, Dict


VALID_SIZES = ["8.5x11", "8x10", "A4"]
VALID_LANGS = ["English", "Hindi"]


def validate_book_request(data: Dict[str, Any]) -> Dict[str, Any]:
    errors = []
    pages = data.get("page_count", 20)
    try:
        pages = int(pages)
        if not (1 <= pages <= 200):
            errors.append("page_count must be 1-200")
    except (TypeError, ValueError):
        errors.append("page_count must be integer")

    size = data.get("book_size", "8.5x11")
    if size not in VALID_SIZES:
        errors.append(f"book_size must be one of {VALID_SIZES}")

    lang = data.get("language", "English")
    if lang not in VALID_LANGS:
        errors.append(f"language must be one of {VALID_LANGS}")

    if not data.get("topic"):
        errors.append("topic is required")

    return {"ok": not errors, "errors": errors}