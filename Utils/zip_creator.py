"""Pack a completed book into a ZIP."""
import logging
import zipfile
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def create_book_zip(workspace: Path, zip_path: Path) -> str:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in workspace.rglob("*"):
            if f.is_file() and not f.name.endswith(".zip"):
                zf.write(f, arcname=str(f.relative_to(workspace.parent)))
    logger.info("ZIP created: %s", zip_path)
    return str(zip_path)