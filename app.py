"""Flask web dashboard entry."""
import logging
from flask import Flask
from config import Config
from Database.mongodb import connect, close
from Database.migrations import run_migrations
from Dashboard.auth import init_auth
from Dashboard.routes import init_routes

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL, logging.INFO))
logger = logging.getLogger("app")


def create_app() -> Flask:
    app = Flask(__name__, template_folder="Dashboard/templates",
                static_folder="Dashboard/static")
    app.config["SECRET_KEY"] = Config.FLASK_SECRET_KEY
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    if not connect():
        logger.error("Cannot start app — MongoDB unavailable")

    run_migrations()
    init_auth(app)
    init_routes(app)
    return app


if __name__ == "__main__":
    app = create_app()
    try:
        app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=False)
    finally:
        close()