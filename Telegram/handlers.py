```python
"""All Telegram handlers."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from Database.repositories import (
    UserRepository,
    SettingsRepository,
    BookRepository,
    JobRepository,
    AIProviderRepository,
)
from Storage.storage_manager import get_storage
from Telegram import keyboards as kb
from Telegram import states as st

logger = logging.getLogger(__name__)


# ---------- Helpers ----------

def _authorized(update: Update) -> bool:
    user = update.effective_user

    if not user:
        return False

    allowed = Config.TELEGRAM_ALLOWED_USER_IDS

    if not allowed:
        return True

    return user.id in allowed


async def _reply(update: Update, text: str, markup=None):
    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=markup
        )


async def _ensure_user(update: Update):
    user = update.effective_user

    if not user:
        return

    UserRepository().get_or_create(
        user.id,
        user.username or "",
        user.first_name or ""
    )


# ---------- Start / Menu ----------

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _authorized(update):
        await _reply(update, "⛔ You are not authorized.")
        return

    await _ensure_user(update)

    uid = update.effective_user.id
    settings = SettingsRepository().get(uid)

    await _reply(
        update,
        f"👋 Welcome to AI Coloring Book Factory!\n\n"
        f"🆔 Your ID: {uid}\n"
        f"📄 Default pages: {settings['default_pages']}\n"
        f"🌐 Language: {settings['language']}\n"
        f"🤖 Provider: {settings.get('ai_provider', 'pollinations')}\n\n"
        f"Use the buttons below 👇",
        kb.main_menu()
    )

    ctx.user_data["state"] = st.MAIN_MENU


async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _authorized(update):
        return

    await _reply(update, "📋 Main Menu", kb.main_menu())
    ctx.user_data["state"] = st.MAIN_MENU


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _authorized(update):
        return

    help_text = (
        "❓ Help\n\n"
        "📚 Create New Book — create a new book job\n"
        "⚙️ Settings — change book settings\n"
        "📖 My Books — view your books\n"
        "🎨 Generate Cover — covers are generated with books\n"
        "👁 Preview — download latest preview\n"
        "📊 Book Status — check job progress\n"
        "📦 Download ZIP — download completed book\n"
        "🤖 AI Provider — select image AI\n\n"
        "Commands:\n"
        "/start /menu /create /settings /pages /theme "
        "/cover /preview /status /download /history "
        "/provider /help /cancel"
    )

    await _reply(update, help_text, kb.main_menu())


async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _authorized(update):
        return

    ctx.user_data.clear()

    await _reply(
        update,
        "❌ Cancelled. Back to main menu.",
        kb.main_menu()
    )


# ---------- Main Menu Router ----------

async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _authorized(update):
        return

    if not update.message or not update.message.text:
        return

    await _ensure_user(update)

    text = update.message.text.strip()
    uid = update.effective_user.id

    # Main menu

    if text == "📚 Create New Book":
        ctx.user_data["state"] = st.BOOK_TOPIC

        await _reply(
            update,
            "🎨 Choose a topic:",
            kb.book_creation_menu()
        )
        return

    if text == "⚙️ Settings":
        ctx.user_data["state"] = st.SETTINGS

        await _reply(
            update,
            "⚙️ Settings Menu",
            kb.settings_menu()
        )
        return

    if text == "📖 My Books":
        await _show_my_books(update)
        return

    if text == "🤖 AI Provider":
        ctx.user_data["state"] = st.AI_PROVIDER_MENU

        await _reply(
            update,
            "🤖 Choose AI Provider:",
            kb.ai_provider_menu()
        )
        return

    if text == "📊 Book Status":
        await _show_status(update)
        return

    if text == "📦 Download ZIP":
        ctx.user_data["state"] = st.DOWNLOAD_MENU

        await _reply(
            update,
            "📦 Download Center",
            kb.download_menu()
        )
        return

    if text == "👁 Preview":
        await _send_latest_file(update, "preview")
        return

    if text == "🎨 Generate Cover":
        await _reply(
            update,
            "🎨 Covers are generated automatically with each book.\n"
            "Open My Books after generation is complete.",
            kb.main_menu()
        )
        return

    if text == "❓ Help":
        await cmd_help(update, ctx)
        return

    if text == "🔙 Main Menu":
        ctx.user_data["state"] = st.MAIN_MENU

        await _reply(
            update,
            "🏠 Main Menu",
            kb.main_menu()
        )
        return

    # Settings menu

    if text == "📄 Number of Pages":
        ctx.user_data["state"] = st.WAIT_PAGES

        await _reply(
            update,
            "Enter number of pages (1-200):"
        )
        return

    if text == "📐 Book Size":
        ctx.user_data["state"] = st.WAIT_BOOK_SIZE

        await _reply(
            update,
            "Choose size:\n8.5x11 / 8x10 / A4"
        )
        return

    if text == "🎯 Target Age":
        ctx.user_data["state"] = st.WAIT_AGE

        await _reply(
            update,
            "Enter target age range (e.g. 4-8):"
        )
        return

    if text == "🎨 Art Style":
        ctx.user_data["state"] = st.WAIT_STYLE

        await _reply(
            update,
            "Enter art style (e.g. Cute Cartoon, Minimalist):"
        )
        return

    if text == "🌐 Language":
        ctx.user_data["state"] = st.WAIT_LANG

        await _reply(
            update,
            "Choose language: English or Hindi"
        )
        return

    if text == "🖤 Black & White":
        settings = SettingsRepository().get(uid)

        new_value = not settings.get("black_white", True)

        SettingsRepository().update(
            uid,
            {"black_white": new_value}
        )

        await _reply(
            update,
            f"🖤 Black & White: {'ON' if new_value else 'OFF'}",
            kb.settings_menu()
        )
        return

    if text == "🖼 Border Settings":
        settings = SettingsRepository().get(uid)

        new_value = not settings.get("border", True)

        SettingsRepository().update(
            uid,
            {"border": new_value}
        )

        await _reply(
            update,
            f"🖼 Border: {'ON' if new_value else 'OFF'}",
            kb.settings_menu()
        )
        return

    if text == "💾 Save Settings":
        await _reply(
            update,
            "💾 Settings are saved automatically.",
            kb.settings_menu()
        )
        return

    if text == "⚙️ Advanced Settings":
        ctx.user_data["state"] = st.ADVANCED

        await _reply(
            update,
            "⚙️ Advanced Settings",
            kb.advanced_settings_menu()
        )
        return

    if text == "📝 Custom Prompts":
        ctx.user_data["state"] = st.WAIT_CUSTOM_PROMPT

        await _reply(
            update,
            "Send your custom prompt addition (or /cancel):"
        )
        return

    # AI Provider menu

    provider_map = {
        "Hugging Face": "huggingface",
        "Pollinations": "pollinations",
        "Gemini": "gemini",
        "Custom API": "custom",
    }

    if text in provider_map:
        AIProviderRepository().set_user_provider(
            uid,
            provider_map[text]
        )

        await _reply(
            update,
            f"✅ Provider set to {text}",
            kb.main_menu()
        )

        ctx.user_data["state"] = st.MAIN_MENU
        return

    if text == "🔄 Auto Select":
        try:
            from AI.provider_manager import ProviderManager

            provider = ProviderManager().auto_select()

            AIProviderRepository().set_user_provider(
                uid,
                provider
            )

            await _reply(
                update,
                f"✅ Auto-selected: {provider}",
                kb.main_menu()
            )

        except Exception as exc:
            logger.exception("Provider auto-selection failed")

            await _reply(
                update,
                f"❌ Could not auto-select provider: {exc}",
                kb.ai_provider_menu()
            )

        return

    # Book creation topics

    topic_map = {
        "🐼 Animals": "Animals",
        "🦖 Dinosaurs": "Dinosaurs",
        "🐱 Cute Cats": "Cute Cats",
        "🐶 Cute Dogs": "Cute Dogs",
        "🌸 Mandala": "Mandala",
        "🚗 Vehicles": "Vehicles",
        "🌳 Nature": "Nature",
    }

    if text in topic_map:
        await _start_book_creation(
            update,
            ctx,
            topic_map[text]
        )
        return

    if text == "✏️ Custom Topic":
        ctx.user_data["state"] = st.BOOK_CUSTOM_TOPIC

        await _reply(
            update,
            "✏️ Type your custom topic:"
        )
        return

    # Download menu

    download_map = {
        "📕 Interior PDF": "interior",
        "🎨 Front Cover": "front_cover",
        "📘 Back Cover": "back_cover",
        "🖼 Full Wrap Cover": "full_wrap",
        "📦 Complete ZIP": "zip",
    }

    if text in download_map:
        await _send_latest_file(
            update,
            download_map[text]
        )
        return

    # Free-text state handlers

    state = ctx.user_data.get("state", st.MAIN_MENU)

    if state == st.WAIT_PAGES:
        try:
            pages = int(text)

            if not 1 <= pages <= 200:
                raise ValueError

            SettingsRepository().update(
                uid,
                {"default_pages": pages}
            )

            await _reply(
                update,
                f"✅ Pages set to {pages}",
                kb.settings_menu()
            )

        except ValueError:
            await _reply(
                update,
                "❌ Enter a number between 1 and 200."
            )

        ctx.user_data["state"] = st.SETTINGS
        return

    if state == st.WAIT_BOOK_SIZE:
        if text in ("8.5x11", "8x10", "A4"):
            SettingsRepository().update(
                uid,
                {"book_size": text}
            )

            await _reply(
                update,
                f"✅ Size set to {text}",
                kb.settings_menu()
            )
        else:
            await _reply(
                update,
                "❌ Choose 8.5x11, 8x10, or A4."
            )

        ctx.user_data["state"] = st.SETTINGS
        return

    if state == st.WAIT_AGE:
        SettingsRepository().update(
            uid,
            {"target_age": text}
        )

        await _reply(
            update,
            f"✅ Target age set to {text}",
            kb.settings_menu()
        )

        ctx.user_data["state"] = st.SETTINGS
        return

    if state == st.WAIT_STYLE:
        SettingsRepository().update(
            uid,
            {"art_style": text}
        )

        await _reply(
            update,
            f"✅ Art style set to {text}",
            kb.settings_menu()
        )

        ctx.user_data["state"] = st.SETTINGS
        return

    if state == st.WAIT_LANG:
        if text in ("English", "Hindi"):
            SettingsRepository().update(
                uid,
                {"language": text}
            )

            await _reply(
                update,
                f"✅ Language set to {text}",
                kb.settings_menu()
            )
        else:
            await _reply(
                update,
                "❌ Choose English or Hindi."
            )

        ctx.user_data["state"] = st.SETTINGS
        return

    if state == st.WAIT_CUSTOM_PROMPT:
        ctx.user_data["custom_prompt"] = text

        await _reply(
            update,
            "✅ Custom prompt stored for the next book.",
            kb.main_menu()
        )

        ctx.user_data["state"] = st.MAIN_MENU
        return

    if state == st.BOOK_CUSTOM_TOPIC:
        await _start_book_creation(
            update,
            ctx,
            text
        )
        return

    await _reply(
        update,
        "Use the menu buttons 👇",
        kb.main_menu()
    )


# ---------- Book Creation Queue ----------

async def _start_book_creation(
    update: Update,
    ctx: ContextTypes.DEFAULT_TYPE,
    topic: str
):
    """
    Create a book and job in MongoDB.

    IMPORTANT:
    This function only queues the job.
    GitHub Actions worker is responsible for generation.
    """

    uid = update.effective_user.id

    settings = SettingsRepository().get(uid)

    job_repo = JobRepository()
    book_repo = BookRepository()

    # Prevent multiple active jobs for the same user.
    active_job = job_repo.active_for_user(uid)

    if active_job:
        await _reply(
            update,
            (
                "⚠️ You already have an active book job.\n\n"
                f"Status: {active_job.get('status', 'UNKNOWN')}\n"
                f"Stage: {active_job.get('stage', 'unknown')}\n\n"
                "Please wait until it finishes."
            ),
            kb.main_menu()
        )
        return

    book_id = None

    try:
        # Create book record.
        book_id = book_repo.create({
            "user_id": str(uid),
            "telegram_user_id": uid,
            "title": f"{topic} Coloring Book",
            "topic": topic,
            "page_count": settings["default_pages"],
            "book_size": settings["book_size"],
            "ai_provider": settings.get(
                "ai_provider",
                "pollinations"
            ),
            "status": "QUEUED",
            "settings_snapshot": settings,
            "files": {},
            "metadata": {},
        })

        # Create queued job.
        job_id = job_repo.create({
            "book_id": book_id,
            "user_id": str(uid),
            "telegram_user_id": uid,
            "status": "QUEUED",
            "stage": "queued",
            "progress": 0,
        })

        ctx.user_data["last_book_id"] = book_id
        ctx.user_data["last_job_id"] = job_id
        ctx.user_data["state"] = st.MAIN_MENU

        await _reply(
            update,
            (
                "✅ Your coloring book request has been added!\n\n"
                f"📚 Topic: {topic}\n"
                f"📄 Pages: {settings['default_pages']}\n"
                f"📐 Size: {settings['book_size']}\n"
                f"🎨 Style: {settings['art_style']}\n\n"
                "📥 Job Status: QUEUED\n\n"
                "🤖 GitHub Actions worker will process your request.\n"
                "Use 📊 Book Status to check progress.\n"
                "Use 📖 My Books to view your books."
            ),
            kb.main_menu()
        )

        logger.info(
            "Book queued successfully: book_id=%s job_id=%s user_id=%s",
            book_id,
            job_id,
            uid
        )

    except Exception as exc:
        logger.exception("Could not queue book")

        # Mark book failed if it was already created.
        if book_id:
            try:
                book_repo.update(
                    book_id,
                    {"status": "FAILED"}
                )
            except Exception:
                logger.exception(
                    "Could not mark book as failed"
                )

        await _reply(
            update,
            f"❌ Could not create book request: {exc}",
            kb.main_menu()
        )


# ---------- My Books ----------

async def _show_my_books(update: Update):
    uid = update.effective_user.id

    books = BookRepository().list_by_user(
        uid,
        limit=15
    )

    if not books:
        await _reply(
            update,
            "📚 No books yet. Create one!",
            kb.main_menu()
        )
        return

    lines = ["📚 Your Books:\n"]

    for book in books:
        title = book.get("title", "Untitled")
        status = book.get("status", "UNKNOWN")

        created_at = book.get("created_at")

        if created_at:
            try:
                date_text = created_at.strftime("%Y-%m-%d")
            except Exception:
                date_text = str(created_at)
        else:
            date_text = "Unknown date"

        lines.append(
            f"• {title} — {status} ({date_text})"
        )

    await _reply(
        update,
        "\n".join(lines),
        kb.main_menu()
    )


# ---------- Job Status ----------

async def _show_status(update: Update):
    uid = update.effective_user.id

    jobs = JobRepository().list_by_user(
        uid,
        limit=5
    )

    if not jobs:
        await _reply(
            update,
            "📊 No jobs found.",
            kb.main_menu()
        )
        return

    lines = ["📊 Recent Jobs:\n"]

    for job in jobs:
        status = job.get("status", "UNKNOWN")
        stage = job.get("stage", "")
        progress = job.get("progress", 0)

        lines.append(
            f"• {status} — {stage} ({progress}%)"
        )

        error = job.get("error")

        if error:
            lines.append(f"  Error: {error}")

    await _reply(
        update,
        "\n".join(lines),
        kb.main_menu()
    )


# ---------- Download Latest File ----------

async def _send_latest_file(
    update: Update,
    kind: str
):
    uid = update.effective_user.id

    books = BookRepository().list_by_user(
        uid,
        limit=15
    )

    if not books:
        await _reply(
            update,
            "📚 No books found.",
            kb.main_menu()
        )
        return

    # Find the newest completed book containing this file.
    selected_book = None
    location = None

    for book in books:
        if book.get("status") != "COMPLETED":
            continue

        files = book.get("files", {})
        candidate = files.get(kind)

        if candidate:
            selected_book = book
            location = candidate
            break

    if not selected_book or not location:
        await _reply(
            update,
            f"❌ {kind} is not available yet.",
            kb.main_menu()
        )
        return

    try:
        import io

        data = get_storage().get_bytes(location)

        extension = "zip" if kind == "zip" else "pdf"

        document = io.BytesIO(data)
        document.name = f"{kind}.{extension}"

        await update.message.reply_document(
            document,
            filename=document.name
        )

    except Exception as exc:
        logger.exception("File download failed")

        await _reply(
            update,
            f"❌ Download failed: {exc}",
            kb.main_menu()
        )


# ---------- Command Aliases ----------

cmd_create = on_text
cmd_settings = on_text
cmd_pages = on_text
cmd_theme = on_text
cmd_cover = on_text
cmd_preview = on_text
cmd_download = on_text
cmd_provider = on_text


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _authorized(update):
        return

    await _show_status(update)


async def cmd_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _authorized(update):
        return

    await _show_my_books(update)
```