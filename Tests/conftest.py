"""Test fixtures — uses in-memory mongomock if available, else skips."""
import os
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mock_settings():
    return {
        "default_pages": 5,
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