"""Book workspace setup and safe path helpers."""
import logging
import re
import shutil
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)


def safe_name(name: str, max_len: int = 60) -> str:
    s = re.sub(r"[^A-Za-z0-9 _-]", "", name).strip().replace(" ", "_")
    return (s or "book")[:max_len]


def create_book_workspace(book_id: str, title: str) -> Path:
    root = Config.OUTPUT_DIR / f"{safe_name(title, 40)}_{book_id[:8]}"
    root.mkdir(parents=True, exist_ok=True)
    (root / "Images").mkdir(exist_ok=True)
    (root / "Metadata").mkdir(exist_ok=True)
    (root / "Prompts").mkdir(exist_ok=True)
    return root


def cleanup_workspace(path: Path) -> None:
    try:
        if path.exists():
            shutil.rmtree(path)
    except Exception as e:
        logger.warning("cleanup failed: %s", e)