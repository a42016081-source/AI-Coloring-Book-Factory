"""MongoDB connection manager with pooling, retries, and health checks."""
import logging
import time
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import Config

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None
_db = None


def connect(retries: int = 5, backoff: float = 1.5) -> bool:
    global _client, _db
    if not Config.MONGODB_URI:
        logger.error("MONGODB_URI is not set")
        return False
    delay = 1.0
    for attempt in range(1, retries + 1):
        try:
            _client = MongoClient(
                Config.MONGODB_URI,
                maxPoolSize=50,
                minPoolSize=5,
                serverSelectionTimeoutMS=8000,
                connectTimeoutMS=8000,
                socketTimeoutMS=30000,
                retryWrites=True,
                tz_aware=True,
            )
            _client.admin.command("ping")
            _db = _client[Config.MONGODB_DATABASE]
            logger.info("MongoDB connected: %s", Config.MONGODB_DATABASE)
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning("MongoDB attempt %d/%d failed: %s", attempt, retries, e)
            time.sleep(delay)
            delay *= backoff
    logger.error("MongoDB connection failed after %d attempts", retries)
    return False


def get_db():
    if _db is None:
        raise RuntimeError("MongoDB not connected. Call connect() first.")
    return _db


def get_client():
    if _client is None:
        raise RuntimeError("MongoDB not connected.")
    return _client


def is_healthy() -> bool:
    try:
        if _client is None:
            return False
        _client.admin.command("ping")
        return True
    except Exception:
        return False


def close():
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")