"""Manages AI providers, health checks, fallback, and selection."""
import logging
import time
from typing import Dict, List, Optional
from config import Config
from Database.repositories import SettingsRepository, AIProviderRepository

logger = logging.getLogger(__name__)

PROVIDERS = ["huggingface", "pollinations", "gemini", "custom"]
FALLBACK_ORDER = ["pollinations", "huggingface", "gemini", "custom"]


class ProviderManager:
    def __init__(self):
        self._health: Dict[str, Dict] = {}

    def list_providers(self) -> List[str]:
        return list(PROVIDERS)

    def health_check(self, provider: str) -> bool:
        try:
            ok = False
            if provider == "pollinations":
                ok = True  # public endpoint, no auth
            elif provider == "huggingface":
                ok = bool(Config.HF_TOKEN)
            elif provider == "gemini":
                ok = bool(Config.GEMINI_API_KEY)
            elif provider == "custom":
                ok = bool(Config.CUSTOM_IMAGE_API_URL)
            self._health[provider] = {"ok": ok, "checked_at": time.time()}
            return ok
        except Exception as e:
            logger.warning("Health check failed for %s: %s", provider, e)
            return False

    def pick_for_user(self, telegram_user_id: int) -> str:
        settings = SettingsRepository().get(telegram_user_id)
        preferred = settings.get("ai_provider", Config.DEFAULT_AI_PROVIDER)
        if self.health_check(preferred):
            return preferred
        for p in FALLBACK_ORDER:
            if self.health_check(p):
                logger.info("Falling back to provider: %s", p)
                return p
        return "pollinations"

    def auto_select(self) -> str:
        for p in FALLBACK_ORDER:
            if self.health_check(p):
                return p
        return "pollinations"