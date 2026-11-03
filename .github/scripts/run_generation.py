"""GitHub Actions entry point — reads env, uses MongoDB-saved settings, generates book."""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.abspath("."))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("action")


def main():
    from Database.mongodb import connect, close
    from Database.migrations import run_migrations
    from Database.repositories import (
        SettingsRepository, BookRepository, JobRepository, FileRepository,
    )
    from AI.prompt_generator import (generate_page_prompts, generate_cover_prompt,
                                     generate_back_prompt)
    from AI.image_generator import generate_image, to_coloring_page
    from AI.quality_checker import compute_hash, is_duplicate
    from PDF.pdf_creator import create_interior_pdf
    from PDF.cover_creator import (create_front_cover, create_back_cover,
                                    create_full_wrap)
    from PDF.preview_creator import create_preview
    from Metadata.metadata_generator import build_metadata, write_metadata_files
    from Utils.file_manager import create_book_workspace
    from Utils.zip_creator import create_book_zip
    from Storage.storage_manager import get_storage

    if not connect():
        logger.error("MongoDB unavailable")
        sys.exit(1)
    try:
        run_migrations()

        uid = int(os.getenv("UID", "0"))
        settings = SettingsRepository().get(uid)  # falls back to defaults only if truly missing

        topic = os.getenv("TOPIC") or "Animals"
        pages = int(os.getenv("PAGES") or settings["default_pages"])
        size = os.getenv("SIZE") or settings["book_size"]
        style = os.getenv("STYLE") or settings["art_style"]
        age = os.getenv("AGE") or settings["target_age"]
        provider = settings.get("ai_provider", "pollinations")

        book_repo = BookRepository()
        job_repo = JobRepository()
        file_repo = FileRepository()

        existing_id = os.getenv("BOOK_ID")
        book = book_repo.get(existing_id) if existing_id else None
        if not book:
            book_id = book_repo.create({
                "user_id": str(uid),
                "telegram_user_id": uid,
                "title": f"{topic} Coloring Book",
                "topic": topic,
                "page_count": pages,
                "book_size": size,
                "ai_provider": provider,
                "status": "RUNNING",
                "files": {},
                "metadata": {},
            })
        else:
            book_id = book["book_id"]
            book_repo.update(book_id, {"status": "RUNNING"})

        job_id = job_repo.create({
            "book_id": book_id,
            "user_id": str(uid),
            "telegram_user_id": uid,
            "status": "RUNNING",
            "stage": "start",
            "progress": 5,
        })

        ws = create_book_workspace(book_id, topic)
        img_dir = ws / "Images"
        prompts = generate_page_prompts(topic, pages, style, age,
                                        settings["difficulty"], settings["language"])
        (ws / "Prompts" / "image_prompts.txt").write_text(
            "\n\n".join(prompts), encoding="utf-8")

        paths, hashes = [], []
        for i, p in enumerate(prompts):
            try:
                raw = generate_image(p, provider=provider, retries=2, fallback=True)
                h = compute_hash(raw)
                if is_duplicate(h, hashes):
                    raw = generate_image(p + " unique", provider=provider)
                    h = compute_hash(raw)
                hashes.append(h)
                img = to_coloring_page(raw, settings["black_white"], settings["border"])
                path = img_dir / f"Page_{i+1:03d}.png"
                img.save(path)
                paths.append(str(path))
            except Exception as e:
                logger.warning("page %d failed: %s", i+1, e)
            job_repo.update_status(job_id, "RUNNING",
                                   stage=f"image {i+1}/{pages}",
                                   progress=10 + int(60*(i+1)/pages))

        if len(paths) < max(1, pages // 2):
            raise RuntimeError(f"Too many failures: {len(paths)}/{pages}")

        interior = ws / "Interior.pdf"
        create_interior_pdf(paths, str(interior), size, topic)

        cover_art = ws / "cover_art.png"
        back_art = ws / "back_art.png"
        try:
            cover_art.write_bytes(generate_image(
                generate_cover_prompt(topic, style), provider=provider))
            back_art.write_bytes(generate_image(
                generate_back_prompt(topic), provider=provider))
        except Exception as e:
            logger.warning("cover art failed: %s", e)

        front = ws / "Front_Cover.pdf"
        back = ws / "Back_Cover.pdf"
        full = ws / "Full_Wrap_Cover.pdf"
        create_front_cover(topic, "A Fun Coloring Adventure", age,
                          str(cover_art), str(front), size)
        create_back_cover(
            f"Enjoy {len(paths)} original {topic.lower()} coloring pages.",
            [f"{len(paths)} pages", "Single-sided", "Thick outlines"],
            str(back_art), str(back), size)
        create_full_wrap(str(front), str(back), len(paths), str(full), size)

        meta = build_metadata(topic, topic, len(paths), age, size, style,
                             settings["language"])
        write_metadata_files(meta, str(ws / "Metadata"))

        preview = ws / "Preview.pdf"
        create_preview(paths, str(cover_art), str(preview), topic)

        (ws / "README.txt").write_text(f"{topic} Coloring Book\n\n{len(paths)} pages\n",
                                       encoding="utf-8")

        zip_path = ws.parent / f"{topic.replace(' ', '_')}_{book_id[:8]}.zip"
        create_book_zip(ws, zip_path)

        storage = get_storage()
        files = {}
        for label, fp, ftype in [
            ("interior", interior, "pdf"),
            ("front_cover", front, "pdf"),
            ("back_cover", back, "pdf"),
            ("full_wrap", full, "pdf"),
            ("preview", preview, "pdf"),
            ("zip", zip_path, "zip"),
        ]:
            if fp.exists():
                sname, loc = storage.upload(str(fp), book_id, fp.name)
                file_repo.record(book_id, fp.name, ftype, sname, loc,
                               fp.stat().st_size)
                files[label] = loc

        book_repo.update(book_id, {"status": "COMPLETED", "files": files,
                                   "metadata": {k: v for k, v in meta.items()
                                                if not k.startswith("_")}})
        job_repo.update_status(job_id, "COMPLETED", stage="done", progress=100)

        # Notify telegram
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if token and uid:
            try:
                import requests
                requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data={"chat_id": uid,
                          "text": f"✅ Book '{topic}' ready! Use 📦 Download ZIP."},
                    timeout=20,
                )
            except Exception as e:
                logger.warning("Telegram notify failed: %s", e)

    except Exception as e:
        logger.exception("Generation failed")
        sys.exit(1)
    finally:
        close()


if __name__ == "__main__":
    main()