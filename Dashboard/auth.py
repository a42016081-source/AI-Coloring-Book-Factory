"""Simple single-user session-based auth with CSRF protection."""
import hmac
import secrets
from functools import wraps
from flask import session, redirect, url_for, request, render_template, abort
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config


_PASSWORD_HASH = generate_password_hash(Config.FLASK_PASSWORD)


def init_auth(app):
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            csrf = request.form.get("_csrf", "")
            if not _verify_csrf(csrf):
                return render_template("login.html", error="Invalid CSRF token",
                                     csrf=_csrf_token())
            if (username == Config.FLASK_USERNAME
                    and check_password_hash(_PASSWORD_HASH, password)):
                session["user"] = username
                session["csrf"] = _csrf_token()
                return redirect(url_for("dashboard_home"))
            return render_template("login.html", error="Invalid credentials",
                                 csrf=_csrf_token())
        return render_template("login.html", csrf=_csrf_token())

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.before_request
    def protect():
        if request.path in ("/login", "/static") or request.path.startswith("/static"):
            return
        if "user" not in session:
            return redirect(url_for("login"))


def _csrf_token() -> str:
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def _verify_csrf(token: str) -> bool:
    return hmac.compare_digest(token, session.get("csrf", ""))


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper