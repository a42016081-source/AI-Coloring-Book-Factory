"""All dashboard routes."""
import logging
import uuid
from flask import (render_template, request, jsonify, session,
                   redirect, url_for, send_file, abort)
from config import Config
from Database.repositories import (
    SettingsRepository, BookRepository, JobRepository,
    AIProviderRepository, ActivityLogRepository,
)
from Database.mongodb import is_healthy
from Storage.storage_manager import get_storage
from Dashboard.auth import login_required, _csrf_token, _verify_csrf

logger = logging.getLogger(__name__)


def init_routes(app):

    def _uid():
        return str(session.get("user", "dashboard"))

    @app.route("/")
    @login_required
    def dashboard_home():
        settings = SettingsRepository().get(0)  # dashboard uses telegram_user_id 0
        books = BookRepository().list_by_user(0, limit=10)
        jobs = JobRepository().list_by_user(0, limit=10)
        return render_template("dashboard.html", settings=settings,
                             books=books, jobs=jobs,
                             db_ok=is_healthy(), csrf=_csrf_token())

    @app.route("/create", methods=["GET", "POST"])
    @login_required
    def create_book():
        if request.method == "POST":
            if not _verify_csrf(request.form.get("_csrf", "")):
                return "CSRF error", 400
            topic = request.form.get("topic", "Animals")
            settings = SettingsRepository().get(0)
            page_count = int(request.form.get("page_count", settings["default_pages"]))
            book_size = request.form.get("book_size", settings["book_size"])
            age = request.form.get("target_age", settings["target_age"])

            book_id = BookRepository().create({
                "user_id": _uid(),
                "telegram_user_id": 0,
                "title": request.form.get("book_name", f"{topic} Coloring Book"),
                "topic": topic,
                "page_count": page_count,
                "book_size": book_size,
                "target_age": age,
                "ai_provider": settings.get("ai_provider", "pollinations"),
                "status": "QUEUED",
                "files": {},
                "metadata": {},
            })
            job_id = JobRepository().create({
                "book_id": book_id,
                "user_id": _uid(),
                "telegram_user_id": 0,
                "status": "QUEUED",
                "stage": "queued",
                "progress": 0,
            })
            return redirect(url_for("dashboard_home"))
        settings = SettingsRepository().get(0)
        return render_template("create.html", settings=settings,
                             csrf=_csrf_token())

    @app.route("/settings", methods=["POST"])
    @login_required
    def update_settings():
        if not _verify_csrf(request.form.get("_csrf", "")):
            return "CSRF error", 400
        updates = {}
        for k in ["default_pages", "book_size", "target_age", "language",
                  "book_type", "art_style", "difficulty", "image_quality"]:
            if k in request.form:
                v = request.form[k]
                if k == "default_pages":
                    try:
                        v = int(v)
                    except ValueError:
                        continue
                updates[k] = v
        for k in ["black_white", "border", "generate_front_cover",
                  "generate_back_cover", "generate_preview"]:
            if k in request.form:
                updates[k] = request.form[k] in ("on", "true", "1", "yes")
        SettingsRepository().update(0, updates)
        return redirect(url_for("dashboard_home"))

    @app.route("/books")
    @login_required
    def books_list():
        books = BookRepository().list_by_user(0, limit=100)
        return render_template("books.html", books=books, csrf=_csrf_token())

    @app.route("/download/<book_id>/<kind>")
    @login_required
    def download_file(book_id, kind):
        book = BookRepository().get(book_id)
        if not book:
            abort(404)
        loc = book.get("files", {}).get(kind)
        if not loc:
            abort(404)
        try:
            data = get_storage().get_bytes(loc)
        except Exception as e:
            logger.error("Download failed: %s", e)
            abort(500)
        import io
        bio = io.BytesIO(data)
        bio.seek(0)
        ext = "zip" if kind == "zip" else "pdf"
        return send_file(bio, as_attachment=True,
                        download_name=f"{book['title'].replace(' ', '_')}_{kind}.{ext}")

    @app.route("/status")
    @login_required
    def status_page():
        return jsonify({
            "mongo": is_healthy(),
            "database": Config.MONGODB_DATABASE,
        })

    @app.route("/health")
    def health():
        return jsonify({"ok": is_healthy()})

    @app.errorhandler(404)
    def nf(_):
        return render_template("error.html", code=404,
                             message="Not found"), 404