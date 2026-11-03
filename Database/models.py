"""Document schemas with validation helpers."""
from datetime import datetime, timezone
from typing import Any, Dict, List


def _now() -> datetime:
    return datetime.now(timezone.utc)


def default_settings() -> Dict[str, Any]:
    return {
        "default_pages": 20,
        "book_size": "8.5x11",
        "target_age": "4-8",
        "language": "English",
        "book_type": "Coloring Book",
        "art_style": "Cute Cartoon",
        "difficulty": "Easy",
        "black_white": True,
        "border": True,
        "generate_front_cover": True,
        "generate_back_cover": True,
        "generate_preview": True,
        "image_quality": "High",
        "ai_provider": "pollinations",
    }


def validate_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Merge with defaults and coerce types. Returns cleaned dict."""
    base = default_settings()
    base.update({k: v for k, v in settings.items() if k in base or k == "ai_provider"})

    try:
        base["default_pages"] = max(1, min(int(base["default_pages"]), 200))
    except (TypeError, ValueError):
        base["default_pages"] = 20

    if base["book_size"] not in ("8.5x11", "8x10", "A4", "Custom"):
        base["book_size"] = "8.5x11"

    for k in ("black_white", "border", "generate_front_cover",
              "generate_back_cover", "generate_preview"):
        base[k] = bool(base.get(k, True))

    return base


def new_user(telegram_user_id: int, username: str = "", first_name: str = "") -> Dict[str, Any]:
    return {
        "telegram_user_id": telegram_user_id,
        "username": username or "",
        "first_name": first_name or "",
        "created_at": _now(),
        "updated_at": _now(),
    }


def new_book_record(user_id: str, telegram_user_id: int, title: str,
                    topic: str, page_count: int, book_size: str,
                    ai_provider: str) -> Dict[str, Any]:
    return {
        "book_id": None,  # set by repo
        "user_id": user_id,
        "telegram_user_id": telegram_user_id,
        "title": title,
        "topic": topic,
        "page_count": page_count,
        "book_size": book_size,
        "ai_provider": ai_provider,
        "status": "PENDING",
        "files": {},
        "metadata": {},
        "created_at": _now(),
        "updated_at": _now(),
    }


def new_job_record(book_id: str, user_id: str, telegram_user_id: int) -> Dict[str, Any]:
    return {
        "job_id": None,
        "book_id": book_id,
        "user_id": user_id,
        "telegram_user_id": telegram_user_id,
        "status": "QUEUED",
        "stage": "queued",
        "progress": 0,
        "error": None,
        "created_at": _now(),
        "updated_at": _now(),
        "started_at": None,
        "ended_at": None,
    }