"""
auth.py — Login, logout, and the role-based root redirect.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from database import fetch_one, hash_pw, get_setting

auth_bp = Blueprint("auth", __name__)

ROLE_HOME = {
    "superadmin": "superadmin.dashboard",
    "admin": "admin.dashboard",
    "lecturer": "lecturer.dashboard",
    "student": "student.dashboard",
}


@auth_bp.route("/")
def index():
    if session.get("user_id"):
        endpoint = ROLE_HOME.get(session.get("role"))
        if endpoint:
            return redirect(url_for(endpoint))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        endpoint = ROLE_HOME.get(session.get("role"))
        if endpoint:
            return redirect(url_for(endpoint))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")

        user = fetch_one("SELECT * FROM users WHERE username=? AND role=?", (username, role))
        if not user or user["password"] != hash_pw(password):
            flash("Invalid username or password for the selected role.", "error")
            return render_template("login.html", institution_name=get_setting("institution_name", "ARUSHA UNIVERSITY OF HEALTH AND ALLIED SCIENCE"))
        if user.get("status") == "suspended":
            flash("This account has been suspended.", "error")
            return render_template("login.html", institution_name=get_setting("institution_name", "ARUSHA UNIVERSITY OF HEALTH AND ALLIED SCIENCE"))

        session.clear()
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        endpoint = ROLE_HOME.get(user["role"])
        if not endpoint:
            flash(f"Role '{user['role']}' is not recognized.", "error")
            session.clear()
            return render_template("login.html", institution_name=get_setting("institution_name", "ARUSHA UNIVERSITY OF HEALTH AND ALLIED SCIENCE"))
        return redirect(url_for(endpoint))

    return render_template("login.html", institution_name=get_setting("institution_name", "ARUSHA UNIVERSITY OF HEALTH AND ALLIED SCIENCE"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
