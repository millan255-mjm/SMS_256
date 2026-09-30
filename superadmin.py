"""
superadmin.py — Super Admin routes: Manage Admins, Manage All Users,
System Settings, DB Backup/Restore, Reports, Security & Permissions.
"""

import os
import datetime

from flask import (
    Blueprint, request, redirect, url_for, flash, session, send_file
)

from database import (
    DB_FILE,
    fetch_admins, admin_fields, insert_admin, update_admin, delete_admin,
    fetch_all_users, all_users_fields, update_user_any, delete_user_any,
    fetch_one, execute, hash_pw,
    get_setting, set_setting,
)
from helpers import role_required, render_list, render_form, render_template

superadmin_bp = Blueprint("superadmin", __name__)

NAV = [
    {"endpoint": "superadmin.admins_list", "icon": "\U0001F464", "label": "Manage Admins", "key": "admins"},
    {"endpoint": "superadmin.users_list", "icon": "\U0001F465", "label": "Manage All Users", "key": "users"},
    {"endpoint": "superadmin.settings", "icon": "\u2699", "label": "System Settings", "key": "settings"},
    {"endpoint": "superadmin.backup", "icon": "\U0001F4BE", "label": "DB Backup/Restore", "key": "backup"},
    {"endpoint": "superadmin.reports", "icon": "\U0001F4CA", "label": "Reports", "key": "reports"},
    {"endpoint": "superadmin.security", "icon": "\U0001F510", "label": "Security & Permissions", "key": "security"},
]

ADMIN_COLUMNS = [("username", "Username"), ("full_name", "Full Name"), ("email", "Email"), ("status", "Status")]
USER_COLUMNS = [("username", "Username"), ("role", "Role"), ("full_name", "Full Name"),
                ("email", "Email"), ("status", "Status")]


@superadmin_bp.route("/")
@role_required("superadmin")
def dashboard():
    return redirect(url_for("superadmin.admins_list"))


# --- Manage Admins ---
@superadmin_bp.route("/admins")
@role_required("superadmin")
def admins_list():
    q = request.args.get("q", "").strip().lower()
    rows = fetch_admins()
    if q:
        rows = [r for r in rows if q in " ".join(str(v) for v in r.values()).lower()]
    return render_list(NAV, "admins", "Manage Admins", ADMIN_COLUMNS, rows,
                        add_endpoint="superadmin.admins_add",
                        edit_endpoint="superadmin.admins_edit",
                        delete_endpoint="superadmin.admins_delete", search=q)


@superadmin_bp.route("/admins/add", methods=["GET", "POST"])
@role_required("superadmin")
def admins_add():
    if request.method == "POST":
        try:
            insert_admin(request.form)
            flash("Admin added successfully.", "success")
            return redirect(url_for("superadmin.admins_list"))
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
    return render_form(NAV, "admins", "Add Admin", admin_fields(), back_endpoint="superadmin.admins_list")


@superadmin_bp.route("/admins/edit/<int:id>", methods=["GET", "POST"])
@role_required("superadmin")
def admins_edit(id):
    row = fetch_one("SELECT * FROM users WHERE id=? AND role='admin'", (id,))
    if not row:
        flash("Admin not found.", "error")
        return redirect(url_for("superadmin.admins_list"))
    if request.method == "POST":
        try:
            update_admin(id, request.form)
            flash("Admin updated successfully.", "success")
            return redirect(url_for("superadmin.admins_list"))
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
    return render_form(NAV, "admins", "Edit Admin", admin_fields(), initial=row,
                        back_endpoint="superadmin.admins_list")


@superadmin_bp.route("/admins/delete/<int:id>", methods=["POST"])
@role_required("superadmin")
def admins_delete(id):
    delete_admin(id)
    flash("Admin deleted.", "success")
    return redirect(url_for("superadmin.admins_list"))


# --- Manage All Users ---
@superadmin_bp.route("/users")
@role_required("superadmin")
def users_list():
    q = request.args.get("q", "").strip().lower()
    rows = fetch_all_users()
    if q:
        rows = [r for r in rows if q in " ".join(str(v) for v in r.values()).lower()]
    return render_list(NAV, "users", "Manage All Users", USER_COLUMNS, rows,
                        edit_endpoint="superadmin.users_edit",
                        delete_endpoint="superadmin.users_delete",
                        allow_add=False, search=q)


@superadmin_bp.route("/users/edit/<int:id>", methods=["GET", "POST"])
@role_required("superadmin")
def users_edit(id):
    row = fetch_one("SELECT * FROM users WHERE id=?", (id,))
    if not row:
        flash("User not found.", "error")
        return redirect(url_for("superadmin.users_list"))
    if request.method == "POST":
        try:
            update_user_any(id, request.form)
            flash("User updated successfully.", "success")
            return redirect(url_for("superadmin.users_list"))
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
    return render_form(NAV, "users", "Edit User", all_users_fields(), initial=row,
                        back_endpoint="superadmin.users_list")


@superadmin_bp.route("/users/delete/<int:id>", methods=["POST"])
@role_required("superadmin")
def users_delete(id):
    delete_user_any(id)
    flash("User deleted.", "success")
    return redirect(url_for("superadmin.users_list"))


# --- System Settings ---
@superadmin_bp.route("/settings", methods=["GET", "POST"])
@role_required("superadmin")
def settings():
    if request.method == "POST":
        for key in ("institution_name", "academic_year", "contact_email"):
            set_setting(key, request.form.get(key, ""))
        flash("System settings updated successfully.", "success")
        return redirect(url_for("superadmin.settings"))
    current = {
        "institution_name": get_setting("institution_name"),
        "academic_year": get_setting("academic_year"),
        "contact_email": get_setting("contact_email"),
    }
    return render_template("superadmin/settings.html", nav_items=NAV, active="settings",
                            page_title="System Settings", settings=current)


# --- DB Backup / Restore ---
@superadmin_bp.route("/backup")
@role_required("superadmin")
def backup():
    return render_template("superadmin/backup.html", nav_items=NAV, active="backup",
                            page_title="Database Backup & Restore")


@superadmin_bp.route("/backup/download")
@role_required("superadmin")
def backup_download():
    fname = f"sms_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    return send_file(DB_FILE, as_attachment=True, download_name=fname)


@superadmin_bp.route("/backup/restore", methods=["POST"])
@role_required("superadmin")
def backup_restore():
    file = request.files.get("backup_file")
    if not file or not file.filename:
        flash("Please choose a backup file to restore.", "error")
        return redirect(url_for("superadmin.backup"))
    tmp_path = DB_FILE + ".upload_tmp"
    file.save(tmp_path)
    os.replace(tmp_path, DB_FILE)
    flash("Database restored successfully.", "success")
    return redirect(url_for("superadmin.backup"))


# --- Reports ---
@superadmin_bp.route("/reports")
@role_required("superadmin")
def reports():
    from report_utils import build_reports_context
    return render_template("reports.html", **build_reports_context(NAV, "reports"))


# --- Security & Permissions ---
PERMS = [
    ("Super Admin", "Full system access: manage admins, all users, settings, backups, "
                     "security and reports."),
    ("Admin", "Manage students, lecturers, courses, classes, enrollment, attendance "
              "oversight and reports."),
    ("Lecturer", "Manage own courses, record attendance & marks, manage assignments, "
                 "view student performance."),
    ("Student", "View own profile, courses, results, attendance and assignments."),
]


@superadmin_bp.route("/security", methods=["GET", "POST"])
@role_required("superadmin")
def security():
    if request.method == "POST":
        p1 = request.form.get("password1", "")
        p2 = request.form.get("password2", "")
        if not p1 or p1 != p2:
            flash("Passwords do not match or are empty.", "error")
        else:
            execute("UPDATE users SET password=? WHERE id=?", (hash_pw(p1), session["user_id"]))
            flash("Password updated successfully.", "success")
        return redirect(url_for("superadmin.security"))
    return render_template("superadmin/security.html", nav_items=NAV, active="security",
                            page_title="Security & Permissions", perms=PERMS)
