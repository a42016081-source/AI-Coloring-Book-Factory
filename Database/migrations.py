"""One-shot migrations. Safe to re-run."""
import logging
from Database.mongodb import get_db
from Database.indexes import ensure_indexes

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    db = get_db()
    # Seed AI providers on first run
    defaults = [
        {"name": "nvidia", "label": "NVIDIA FLUX", "enabled": True},
        {"name": "huggingface", "label": "Hugging Face", "enabled": True},
        {"name": "pollinations", "label": "Pollinations", "enabled": True},
        {"name": "gemini", "label": "Gemini", "enabled": True},
        {"name": "custom", "label": "Custom API", "enabled": True},
    ]
    for prov in defaults:
        db.ai_providers.update_one(
            {"name": prov["name"]},
            {"$setOnInsert": prov},
            upsert=True,
        )
    ensure_indexes()
    logger.info("Migrations complete")
