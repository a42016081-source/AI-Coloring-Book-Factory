"""Central configuration loaded from environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", BASE_DIR / "output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI", "")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "ai_coloring_book_factory")

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ALLOWED_USER_IDS = [
        int(x.strip()) for x in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",") if x.strip()
    ]

    # Flask
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
    FLASK_USERNAME = os.getenv("FLASK_USERNAME", "admin")
    FLASK_PASSWORD = os.getenv("FLASK_PASSWORD", "admin")
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

    # AI
    HF_TOKEN = os.getenv("HF_TOKEN", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    # NVIDIA NIM APIs: FLUX image generation + Llama prompt enhancement
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_FLUX_URL = os.getenv(
        "NVIDIA_FLUX_URL",
        "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev",
    )
    NVIDIA_CHAT_URL = os.getenv(
        "NVIDIA_CHAT_URL", "https://integrate.api.nvidia.com/v1/chat/completions"
    )
    NVIDIA_CHAT_MODEL = os.getenv(
        "NVIDIA_CHAT_MODEL", "meta/llama-3.2-90b-vision-instruct"
    )
    NVIDIA_PROMPT_ENHANCEMENT = os.getenv(
        "NVIDIA_PROMPT_ENHANCEMENT", "true"
    ).lower() in ("1", "true", "yes", "on")
    CUSTOM_IMAGE_API_URL = os.getenv("CUSTOM_IMAGE_API_URL", "")
    CUSTOM_IMAGE_API_KEY = os.getenv("CUSTOM_IMAGE_API_KEY", "")
    DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "pollinations")

    # Storage
    STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "gridfs")
    S3_ENDPOINT = os.getenv("S3_ENDPOINT", "")
    S3_BUCKET = os.getenv("S3_BUCKET", "")
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
    S3_REGION = os.getenv("S3_REGION", "us-east-1")

    # Encryption
    SECRET_ENCRYPTION_KEY = os.getenv("SECRET_ENCRYPTION_KEY", "")

    # Misc
    OUTPUT_DIR = OUTPUT_DIR
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
