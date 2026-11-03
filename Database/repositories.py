"""Repository classes — the ONLY way to touch MongoDB collections."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from Database.mongodb import get_db
from Database.models import default_settings, validate_settings, new_user

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if doc is None:
        return None
    doc = dict(doc)
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc


# ---------------- USER REPOSITORY ----------------

class UserRepository:
    def __init__(self):
        self.col = get_db().users

    def get_by_telegram_id(self, telegram_user_id: int) -> Optional[Dict[str, Any]]:
        return _serialize(self.col.find_one({"telegram_user_id": telegram_user_id}))

    def get_or_create(self, telegram_user_id: int, username: str = "",
                      first_name: str = "") -> Dict[str, Any]:
        existing = self.col.find_one({"telegram_user_id": telegram_user_id})
        if existing:
            # Update but NEVER overwrite settings-ish fields
            self.col.update_one(
                {"_id": existing["_id"]},
                {"$set": {"username": username or existing.get("username", ""),
                          "first_name": first_name or existing.get("first_name", ""),
                          "updated_at": _now()}},
            )
            return _serialize(self.col.find_one({"_id": existing["_id"]}))
        doc = new_user(telegram_user_id, username, first_name)
        res = self.col.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc


# ---------------- SETTINGS REPOSITORY ----------------

class SettingsRepository:
    def __init__(self):
        self.col = get_db().user_settings

    def get(self, telegram_user_id: int) -> Dict[str, Any]:
        """Returns settings for user. If missing, creates defaults.
        NEVER overwrites existing settings."""
        existing = self.col.find_one({"telegram_user_id": telegram_user_id})
        if existing:
            return validate_settings(existing.get("settings", {}))
        defaults = default_settings()
        self.col.insert_one({
            "telegram_user_id": telegram_user_id,
            "settings": defaults,
            "created_at": _now(),
            "updated_at": _now(),
        })
        return defaults

    def update(self, telegram_user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Atomic partial update. Returns full settings."""
        current = self.get(telegram_user_id)
        current.update(updates)
        cleaned = validate_settings(current)
        self.col.update_one(
            {"telegram_user_id": telegram_user_id},
            {"$set": {"settings": cleaned, "updated_at": _now()}},
            upsert=True,
        )
        return cleaned

    def set_provider(self, telegram_user_id: int, provider: str) -> None:
        self.update(telegram_user_id, {"ai_provider": provider})


# ---------------- AI PROVIDER REPOSITORY ----------------

class AIProviderRepository:
    def __init__(self):
        self.col = get_db().ai_providers

    def list_all(self) -> List[Dict[str, Any]]:
        return [_serialize(d) for d in self.col.find({})]

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        return _serialize(self.col.find_one({"name": name}))

    def set_user_provider(self, telegram_user_id: int, provider: str) -> None:
        SettingsRepository().set_provider(telegram_user_id, provider)


# ---------------- BOOK REPOSITORY ----------------

class BookRepository:
    def __init__(self):
        self.col = get_db().books

    def create(self, data: Dict[str, Any]) -> str:
        if not data.get("book_id"):
            data["book_id"] = str(uuid.uuid4())
        data.setdefault("created_at", _now())
        data["updated_at"] = _now()
        self.col.insert_one(data)
        return data["book_id"]

    def get(self, book_id: str) -> Optional[Dict[str, Any]]:
        return _serialize(self.col.find_one({"book_id": book_id}))

    def list_by_user(self, telegram_user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        cur = self.col.find({"telegram_user_id": telegram_user_id}).sort(
            "created_at", -1).limit(limit)
        return [_serialize(d) for d in cur]

    def update(self, book_id: str, updates: Dict[str, Any]) -> None:
        updates = dict(updates)
        updates["updated_at"] = _now()
        self.col.update_one({"book_id": book_id}, {"$set": updates})

    def delete(self, book_id: str) -> None:
        self.col.delete_one({"book_id": book_id})


# ---------------- JOB REPOSITORY ----------------

class JobRepository:
    def __init__(self):
        self.col = get_db().book_jobs

    def create(self, data: Dict[str, Any]) -> str:
        if not data.get("job_id"):
            data["job_id"] = str(uuid.uuid4())
        data.setdefault("created_at", _now())
        data["updated_at"] = _now()
        self.col.insert_one(data)
        return data["job_id"]

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        return _serialize(self.col.find_one({"job_id": job_id}))

    def latest_for_book(self, book_id: str) -> Optional[Dict[str, Any]]:
        return _serialize(self.col.find_one(
            {"book_id": book_id}, sort=[("created_at", -1)]))

    def list_by_user(self, telegram_user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        cur = self.col.find({"telegram_user_id": telegram_user_id}).sort(
            "created_at", -1).limit(limit)
        return [_serialize(d) for d in cur]

    def update_status(self, job_id: str, status: str,
                      stage: Optional[str] = None,
                      progress: Optional[int] = None,
                      error: Optional[str] = None) -> None:
        doc = {"status": status, "updated_at": _now()}
        if stage is not None:
            doc["stage"] = stage
        if progress is not None:
            doc["progress"] = progress
        if error is not None:
            doc["error"] = error
        if status == "RUNNING":
            doc.setdefault("started_at", _now())
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            doc["ended_at"] = _now()
        self.col.update_one({"job_id": job_id}, {"$set": doc})

    def active_for_user(self, telegram_user_id: int) -> Optional[Dict[str, Any]]:
        """Idempotency: prevent duplicate RUNNING jobs."""
        return _serialize(self.col.find_one({
            "telegram_user_id": telegram_user_id,
            "status": {"$in": ["QUEUED", "RUNNING"]},
        }))


# ---------------- FILE REPOSITORY ----------------

class FileRepository:
    def __init__(self):
        self.col = get_db().generated_files

    def record(self, book_id: str, file_name: str, file_type: str,
               storage: str, location: str, size: int) -> str:
        file_id = str(uuid.uuid4())
        self.col.insert_one({
            "file_id": file_id,
            "book_id": book_id,
            "file_name": file_name,
            "file_type": file_type,
            "storage": storage,
            "location": location,
            "size": size,
            "created_at": _now(),
        })
        return file_id

    def list_for_book(self, book_id: str) -> List[Dict[str, Any]]:
        return [_serialize(d) for d in self.col.find({"book_id": book_id})]


# ---------------- ACTIVITY LOG ----------------

class ActivityLogRepository:
    def __init__(self):
        self.col = get_db().activity_logs

    def log(self, user_id: str, action: str, detail: str = "") -> None:
        self.col.insert_one({
            "user_id": user_id,
            "action": action,
            "detail": detail,
            "created_at": _now(),
        })