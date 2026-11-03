"""
GitHub Actions scheduled worker.

Finds QUEUED book jobs in MongoDB, claims them atomically,
generates coloring books, saves files to persistent storage,
updates MongoDB status, and notifies users through Telegram.
"""

import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from pymongo import ReturnDocument

# Make project root importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from Database.mongodb import connect, close, get_db
from Database.migrations import run_migrations
from Database.repositories import (
    SettingsRepository,
    BookRepository,
    JobRepository,
    FileRepository,
)
from AI.prompt_generator import (
    generate_page_prompts,
    generate_cover_prompt,
    generate_back_prompt,
)
from AI.image_generator import generate_image, to_coloring_page
from AI.quality_checker import compute_hash, is_duplicate
from PDF.pdf_creator import create_interior_pdf
from PDF.cover_creator import (
    create_front_cover,
    create_back_cover,
    create_full_wrap,
)
from PDF.preview_creator import create_preview
from Metadata.metadata_generator import (
    build_metadata,
    write_metadata_files,
)
from Utils.file_manager import create_book_workspace
from Utils.zip_creator import create_book_zip
from Storage.storage_manager import get_storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger("pending_worker")


def now():
    return datetime.now(timezone.utc)


def notify_user(uid, message):
    """Send a Telegram message without stopping the worker on failure."""
    token = Config.TELEGRAM_BOT_TOKEN

    if not token or not uid:
        logger.warning("Telegram notification skipped for UID %s", uid)
        return

    try:
        import requests

        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={
                "chat_id": uid,
                "text": message,
            },
            timeout=20,
        )

        response.raise_for_status()

    except Exception:
        logger.exception("Telegram notification failed for UID %s", uid)


def claim_next_job():
    """
    Atomically claim one QUEUED job.
    Prevents two scheduled workers from taking the same job.
    """

    db = get_db()

    job = db.book_jobs.find_one_and_update(
        {"status": "QUEUED"},
        {
            "$set": {
                "status": "RUNNING",
                "stage": "starting",
                "progress": 2,
                "started_at": now(),
                "updated_at": now(),
                "worker": "github-actions",
            }
        },
        sort=[("created_at", 1)],
        return_document=ReturnDocument.AFTER,
    )

    return job


def generate_book(job):
    """Generate one complete book for an existing queued job."""

    job_id = job["job_id"]
    book_id = job["book_id"]
    uid = int(job["telegram_user_id"])

    job_repo = JobRepository()
    book_repo = BookRepository()
    file_repo = FileRepository()

    book = book_repo.get(book_id)

    if not book:
        raise RuntimeError(f"Book not found: {book_id}")

    # Prefer the settings snapshot saved when the user requested the book.
    settings = book.get("settings_snapshot")

    if not settings:
        settings = SettingsRepository().get(uid)

    topic = book.get("topic", "Animals")
    title = book.get("title", f"{topic} Coloring Book")

    pages = int(
        book.get("page_count")
        or settings.get("default_pages", 20)
    )

    size = book.get("book_size") or settings.get("book_size", "8.5x11")
    age = settings.get("target_age", "4-8")
    style = settings.get("art_style", "Cute Cartoon")
    language = settings.get("language", "English")
    difficulty = settings.get("difficulty", "Easy")
    provider = book.get("ai_provider") or settings.get(
        "ai_provider", "pollinations"
    )

    if not 1 <= pages <= 200:
        raise ValueError(f"Invalid page count: {pages}")

    logger.info(
        "Starting job=%s book=%s user=%s topic=%s pages=%s",
        job_id, book_id, uid, topic, pages
    )

    notify_user(
        uid,
        f"🎨 Your coloring book generation has started!\n"
        f"📚 Topic: {topic}\n"
        f"📄 Pages: {pages}"
    )

    job_repo.update_status(
        job_id, "RUNNING", stage="prompts", progress=5
    )

    book_repo.update(book_id, {"status": "RUNNING"})

    # Create workspace
    workspace = create_book_workspace(book_id, topic)
    image_dir = workspace / "Images"
    prompt_dir = workspace / "Prompts"

    image_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)

    # Generate prompts
    prompts = generate_page_prompts(
        topic,
        pages,
        style,
        age,
        difficulty,
        language,
    )

    (prompt_dir / "image_prompts.txt").write_text(
        "\n\n".join(
            f"[{i + 1}] {prompt}"
            for i, prompt in enumerate(prompts)
        ),
        encoding="utf-8",
    )

    # Generate coloring pages
    image_paths = []
    hashes = []

    for index, prompt in enumerate(prompts):

        job_repo.update_status(
            job_id,
            "RUNNING",
            stage=f"image {index + 1}/{pages}",
            progress=10 + int(60 * (index + 1) / pages),
        )

        try:
            raw = generate_image(
                prompt,
                provider=provider,
                retries=2,
                fallback=True,
            )

            image_hash = compute_hash(raw)

            if is_duplicate(image_hash, hashes):
                raw = generate_image(
                    prompt + " unique variation",
                    provider=provider,
                    retries=2,
                    fallback=True,
                )
                image_hash = compute_hash(raw)

            hashes.append(image_hash)

            image = to_coloring_page(
                raw,
                black_white=settings.get("black_white", True),
                border=settings.get("border", True),
            )

            image_path = image_dir / f"Page_{index + 1:03d}.png"
            image.save(image_path)

            image_paths.append(str(image_path))

            logger.info(
                "Generated page %d/%d for book %s",
                index + 1, pages, book_id
            )

        except Exception as error:
            logger.exception(
                "Page %d generation failed: %s",
                index + 1, error
            )

    if len(image_paths) < max(1, pages // 2):
        raise RuntimeError(
            f"Too many image failures: {len(image_paths)}/{pages}"
        )

    # Create interior PDF
    job_repo.update_status(
        job_id, "RUNNING", stage="interior_pdf", progress=72
    )

    interior = workspace / "Interior.pdf"

    create_interior_pdf(
        image_paths,
        str(interior),
        size,
        title,
    )

    # Generate cover artwork
    job_repo.update_status(
        job_id, "RUNNING", stage="covers", progress=78
    )

    cover_art = workspace / "cover_art.png"
    back_art = workspace / "back_art.png"

    try:
        cover_art.write_bytes(
            generate_image(
                generate_cover_prompt(topic, style),
                provider=provider,
                retries=2,
                fallback=True,
            )
        )

        back_art.write_bytes(
            generate_image(
                generate_back_prompt(topic),
                provider=provider,
                retries=2,
                fallback=True,
            )
        )

    except Exception:
        logger.exception("Cover artwork generation failed")

    # Create cover PDFs
    front = workspace / "Front_Cover.pdf"
    back = workspace / "Back_Cover.pdf"
    full = workspace / "Full_Wrap_Cover.pdf"

    create_front_cover(
        title,
        "A Fun Coloring Adventure",
        age,
        str(cover_art),
        str(front),
        size,
    )

    create_back_cover(
        f"Enjoy {len(image_paths)} original {topic.lower()} coloring pages.",
        [
            f"{len(image_paths)} pages",
            "Single-sided",
            "Thick outlines",
        ],
        str(back_art),
        str(back),
        size,
    )

    create_full_wrap(
        str(front),
        str(back),
        len(image_paths),
        str(full),
        size,
    )

    # Generate metadata
    job_repo.update_status(
        job_id, "RUNNING", stage="metadata", progress=85
    )

    metadata = build_metadata(
        topic,
        title,
        len(image_paths),
        age,
        size,
        style,
        language,
    )

    write_metadata_files(
        metadata,
        str(workspace / "Metadata"),
    )

    # Generate preview
    job_repo.update_status(
        job_id, "RUNNING", stage="preview", progress=90
    )

    preview = workspace / "Preview.pdf"

    create_preview(
        image_paths,
        str(cover_art),
        str(preview),
        title,
    )

    # Create README
    (workspace / "README.txt").write_text(
        f"{title}\n\n"
        f"Topic: {topic}\n"
        f"Pages: {len(image_paths)}\n"
        f"Size: {size}\n"
        f"Age: {age}\n"
        f"Style: {style}\n"
        f"Language: {language}\n",
        encoding="utf-8",
    )

    # Create ZIP
    job_repo.update_status(
        job_id, "RUNNING", stage="zip", progress=95
    )

    zip_path = workspace.parent / (
        f"{topic.replace(' ', '_')}_{book_id[:8]}.zip"
    )

    create_book_zip(workspace, zip_path)

    # Upload files to persistent storage
    storage = get_storage()

    files = {}

    generated_files = [
        ("interior", interior, "pdf"),
        ("front_cover", front, "pdf"),
        ("back_cover", back, "pdf"),
        ("full_wrap", full, "pdf"),
        ("preview", preview, "pdf"),
        ("zip", zip_path, "zip"),
    ]

    for label, file_path, file_type in generated_files:

        if not file_path.exists():
            logger.warning("Missing output file: %s", file_path)
            continue

        storage_name, location = storage.upload(
            str(file_path),
            book_id,
            file_path.name,
        )

        file_repo.record(
            book_id,
            file_path.name,
            file_type,
            storage_name,
            location,
            file_path.stat().st_size,
        )

        files[label] = location

    if "zip" not in files:
        raise RuntimeError("ZIP upload failed")

    # Update MongoDB
    book_repo.update(
        book_id,
        {
            "status": "COMPLETED",
            "files": files,
            "metadata": {
                key: value
                for key, value in metadata.items()
                if not key.startswith("_")
            },
            "completed_at": now(),
        },
    )

    job_repo.update_status(
        job_id,
        "COMPLETED",
        stage="done",
        progress=100,
    )

    notify_user(
        uid,
        f"✅ Your coloring book is ready!\n\n"
        f"📚 {title}\n"
        f"📄 Pages: {len(image_paths)}\n"
        f"📦 Complete ZIP has been saved.\n\n"
        f"Open Telegram → Download ZIP to access it."
    )

    logger.info("Job completed successfully: %s", job_id)


def main():

    if not connect():
        logger.error("Could not connect to MongoDB")
        sys.exit(1)

    processed = 0
    failed = 0

    try:
        run_migrations()

        # Process one queued request per scheduled run by default.
        # Set MAX_PENDING_JOBS to process more.
        max_jobs = max(
            1,
            int(os.getenv("MAX_PENDING_JOBS", "1"))
        )

        for _ in range(max_jobs):

            job = claim_next_job()

            if not job:
                logger.info("No pending book requests found.")
                break

            job_id = job["job_id"]
            book_id = job["book_id"]

            try:
                generate_book(job)
                processed += 1

            except Exception as error:

                logger.exception(
                    "Job failed: %s",
                    job_id
                )

                failed += 1

                try:
                    JobRepository().update_status(
                        job_id,
                        "FAILED",
                        error=str(error)[:2000],
                    )

                    BookRepository().update(
                        book_id,
                        {
                            "status": "FAILED",
                            "error": str(error)[:2000],
                        },
                    )

                    uid = int(job.get("telegram_user_id", 0))

                    notify_user(
                        uid,
                        f"❌ Your coloring book could not be generated.\n"
                        f"Error: {str(error)[:500]}"
                    )

                except Exception:
                    logger.exception(
                        "Could not update failed job in MongoDB"
                    )

        logger.info(
            "Worker finished. Processed=%d Failed=%d",
            processed,
            failed,
        )

        # If jobs failed, make GitHub Actions visibly report failure.
        if failed:
            sys.exit(1)

    finally:
        close()


if __name__ == "__main__":
    main()