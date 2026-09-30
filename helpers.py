"""
helpers.py — Auth decorators and small helpers shared by every blueprint.
"""

from functools import wraps
from flask import session, redirect, url_for, render_template, flash

from database import fetch_one


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return fetch_one("SELECT * FROM users WHERE id=?", (uid,))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("auth.login"))
            if session.get("role") not in roles:
                flash("You do not have access to that page.", "error")
                return redirect(url_for("auth.index"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def render_list(nav_items, active, page_title, columns, rows, id_field="id",
                 add_endpoint=None, edit_endpoint=None, delete_endpoint=None,
                 allow_add=True, allow_edit=True, allow_delete=True, search=""):
    return render_template(
        "generic_list.html",
        nav_items=nav_items, active=active, page_title=page_title,
        columns=columns, rows=rows, id_field=id_field,
        add_endpoint=add_endpoint, edit_endpoint=edit_endpoint, delete_endpoint=delete_endpoint,
        allow_add=allow_add, allow_edit=allow_edit, allow_delete=allow_delete, search=search,
    )


def render_form(nav_items, active, page_title, fields, initial=None, back_endpoint=None):
    return render_template(
        "generic_form.html",
        nav_items=nav_items, active=active, page_title=page_title,
        fields=fields, initial=initial or {}, back_endpoint=back_endpoint,
    )
