"""Telegram bot entry point."""
import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
)
from config import Config
from Database.mongodb import connect, close
from Database.migrations import run_migrations
from Telegram import handlers as h

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("bot")


def build_application() -> Application:
    if not Config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    commands = {
        "start": h.cmd_start,
        "menu": h.cmd_menu,
        "help": h.cmd_help,
        "cancel": h.cmd_cancel,
    }
    for name, fn in commands.items():
        app.add_handler(CommandHandler(name, fn))

    # Route /create /settings /pages etc. through on_text for reuse
    for cmd in ["create", "settings", "pages", "theme", "cover",
                "preview", "status", "download", "history", "provider"]:
        app.add_handler(CommandHandler(cmd, h.on_text))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, h.on_text))

    return app


def main():
    if not connect():
        logger.error("Cannot start bot — MongoDB unavailable")
        return
    try:
        run_migrations()
        app = build_application()
        logger.info("Bot starting (polling)...")
        app.run_polling(allowed_updates=["message"])
    finally:
        close()


if __name__ == "__main__":
    main()