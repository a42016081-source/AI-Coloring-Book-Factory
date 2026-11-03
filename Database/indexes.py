"""Create all database indexes."""
import logging
from pymongo import ASCENDING, DESCENDING
from Database.mongodb import get_db

logger = logging.getLogger(__name__)


def ensure_indexes():
    db = get_db()
    # users
    db.users.create_index([("telegram_user_id", ASCENDING)], unique=True, sparse=True)
    db.users.create_index([("username", ASCENDING)], unique=True, sparse=True)

    # user_settings
    db.user_settings.create_index([("telegram_user_id", ASCENDING)], unique=True)
    db.user_settings.create_index([("user_id", ASCENDING)], sparse=True)

    # application_settings
    db.application_settings.create_index([("key", ASCENDING)], unique=True)

    # ai_providers
    db.ai_providers.create_index([("name", ASCENDING)], unique=True)

    # books
    db.books.create_index([("book_id", ASCENDING)], unique=True)
    db.books.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db.books.create_index([("telegram_user_id", ASCENDING), ("created_at", DESCENDING)])

    # book_jobs
    db.book_jobs.create_index([("job_id", ASCENDING)], unique=True)
    db.book_jobs.create_index([("book_id", ASCENDING)])
    db.book_jobs.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db.book_jobs.create_index([("status", ASCENDING)])

    # generated_files
    db.generated_files.create_index([("file_id", ASCENDING)], unique=True)
    db.generated_files.create_index([("book_id", ASCENDING)])
    db.generated_files.create_index([("storage", ASCENDING)])

    # custom_prompts
    db.custom_prompts.create_index([("user_id", ASCENDING), ("name", ASCENDING)], unique=True)

    # telegram_sessions
    db.telegram_sessions.create_index([("telegram_user_id", ASCENDING)], unique=True)

    # dashboard_sessions
    db.dashboard_sessions.create_index([("session_id", ASCENDING)], unique=True)
    db.dashboard_sessions.create_index([("created_at", ASCENDING)], expireAfterSeconds=604800)

    # activity_logs
    db.activity_logs.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db.activity_logs.create_index([("created_at", ASCENDING)], expireAfterSeconds=2592000)

    logger.info("Indexes ensured")