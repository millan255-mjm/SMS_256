"""
app.py — Main Flask application. This is the file Railway (and gunicorn)
run: gunicorn app:app
"""

import os

from flask import Flask, session

from database import init_db, fetch_one
from auth import auth_bp
from superadmin import superadmin_bp
from admin import admin_bp
from lecturer import lecturer_bp
from student import student_bp

ROLE_LABELS = {
    "superadmin": "Super Administrator",
    "admin": "Administrator",
    "lecturer": "Lecturer",
    "student": "Student",
}


def create_app():
    flask_app = Flask(__name__)
    flask_app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me-in-production")

    init_db()

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(superadmin_bp, url_prefix="/superadmin")
    flask_app.register_blueprint(admin_bp, url_prefix="/admin")
    flask_app.register_blueprint(lecturer_bp, url_prefix="/lecturer")
    flask_app.register_blueprint(student_bp, url_prefix="/student")

    @flask_app.context_processor
    def inject_session_user():
        uid = session.get("user_id")
        if not uid:
            return {}
        user = fetch_one("SELECT * FROM users WHERE id=?", (uid,))
        if not user:
            return {}
        return {
            "session_full_name": user["full_name"] or user["username"],
            "session_username": user["username"],
            "session_role_label": ROLE_LABELS.get(user["role"], user["role"]),
        }

    return flask_app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
