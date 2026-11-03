"""Image similarity checks to prevent duplicate pages."""
import io
import logging
from typing import List
import imagehash
from PIL import Image

logger = logging.getLogger(__name__)


def compute_hash(png_bytes: bytes) -> imagehash.ImageHash:
    img = Image.open(io.BytesIO(png_bytes))
    return imagehash.phash(img)


def is_duplicate(new_hash, existing_hashes: List, threshold: int = 5) -> bool:
    for h in existing_hashes:
        if new_hash - h <= threshold:
            return True
    return False


def validate_page(png_bytes: bytes) -> bool:
    try:
        img = Image.open(io.BytesIO(png_bytes))
        img.verify()
        return True
    except Exception as e:
        logger.warning("Invalid image: %s", e)
        return False