"""
student.py — Student routes: My Profile, My Courses, My Results,
My Attendance, My Assignments.
"""

from flask import Blueprint, request, redirect, url_for, flash, session

from database import fetch_all, fetch_one, execute, hash_pw, get_student_record
from helpers import role_required, render_list, render_template

student_bp = Blueprint("student", __name__)

NAV = [
    {"endpoint": "student.profile", "icon": "\U0001F464", "label": "My Profile", "key": "profile"},
    {"endpoint": "student.courses_list", "icon": "\U0001F4DA", "label": "My Courses", "key": "courses"},
    {"endpoint": "student.results_list", "icon": "\U0001F4CA", "label": "My Results", "key": "results"},
    {"endpoint": "student.attendance", "icon": "\U0001F4C5", "label": "My Attendance", "key": "attendance"},
    {"endpoint": "student.assignments_list", "icon": "\U0001F4DD", "label": "My Assignments", "key": "assignments"},
]

COURSE_COLUMNS = [("code", "Code"), ("name", "Course Name"), ("lecturer_name", "Lecturer"),
                   ("credits", "Credits"), ("semester", "Semester")]
RESULT_COLUMNS = [("course_name", "Course"), ("exam_type", "Type"), ("score", "Score"),
                   ("max_score", "Max"), ("date", "Date")]
ASSIGNMENT_COLUMNS = [("title", "Title"), ("course_name", "Course"), ("due_date", "Due Date"),
                       ("description", "Description")]


def _current_student():
    return get_student_record(session["user_id"])


def _require_student():
    student = _current_student()
    if not student:
        flash("No student profile is linked to this account. Please contact an administrator.", "error")
    return student


@student_bp.route("/")
@role_required("student")
def dashboard():
    return redirect(url_for("student.profile"))


@student_bp.route("/profile", methods=["GET", "POST"])
@role_required("student")
def profile():
    student = _require_student()
    if not student:
        return render_template("student/profile.html", nav_items=NAV, active="profile",
                                page_title="My Profile", student=None, class_name=None)

    if request.method == "POST":
        form_kind = request.form.get("form")
        if form_kind == "password":
            p1 = request.form.get("password1", "")
            p2 = request.form.get("password2", "")
            if not p1 or p1 != p2:
                flash("Passwords do not match or are empty.", "error")
            else:
                execute("UPDATE users SET password=? WHERE id=?", (hash_pw(p1), session["user_id"]))
                flash("Password updated successfully.", "success")
        else:
            full_name = request.form.get("full_name", "")
            email = request.form.get("email", "")
            phone = request.form.get("phone", "")
            execute("UPDATE students SET full_name=?, email=?, phone=? WHERE id=?",
                    (full_name, email, phone, student["id"]))
            execute("UPDATE users SET full_name=?, email=? WHERE id=?",
                    (full_name, email, session["user_id"]))
            flash("Profile updated successfully.", "success")
        return redirect(url_for("student.profile"))

    class_row = fetch_one("SELECT name FROM classes WHERE id=?", (student["class_id"],)) if student["class_id"] else None
    return render_template("student/profile.html", nav_items=NAV, active="profile",
                            page_title="My Profile", student=student,
                            class_name=class_row["name"] if class_row else None)


@student_bp.route("/courses")
@role_required("student")
def courses_list():
    student = _require_student()
    rows = []
    if student:
        rows = fetch_all(
            "SELECT co.code, co.name, co.credits, l.full_name AS lecturer_name, e.semester "
            "FROM enrollments e JOIN courses co ON co.id=e.course_id "
            "LEFT JOIN lecturers l ON l.id=co.lecturer_id "
            "WHERE e.student_id=? ORDER BY co.name", (student["id"],))
    return render_list(NAV, "courses", "My Courses", COURSE_COLUMNS, rows,
                        allow_add=False, allow_edit=False, allow_delete=False)


@student_bp.route("/results")
@role_required("student")
def results_list():
    student = _require_student()
    rows = []
    if student:
        rows = fetch_all(
            "SELECT co.name AS course_name, m.exam_type, m.score, m.max_score, m.date "
            "FROM marks m JOIN courses co ON co.id=m.course_id "
            "WHERE m.student_id=? ORDER BY m.date DESC", (student["id"],))
    return render_list(NAV, "results", "My Results", RESULT_COLUMNS, rows,
                        allow_add=False, allow_edit=False, allow_delete=False)


@student_bp.route("/attendance")
@role_required("student")
def attendance():
    student = _require_student()
    records = []
    if student:
        records = fetch_all(
            "SELECT a.date, co.name AS course_name, a.status FROM attendance a "
            "JOIN courses co ON co.id=a.course_id WHERE a.student_id=? ORDER BY a.date DESC",
            (student["id"],))
    total = len(records)
    present = len([r for r in records if r["status"] == "Present"])
    rate = round((present / total) * 100, 1) if total else 0.0
    rate_color = "#2fbf80" if rate >= 75 else ("#ffb648" if rate >= 50 else "#ff5c6c")
    return render_template("student/attendance.html", nav_items=NAV, active="attendance",
                            page_title="My Attendance", records=records, total=total,
                            rate=rate, rate_color=rate_color)


@student_bp.route("/assignments")
@role_required("student")
def assignments_list():
    student = _require_student()
    rows = []
    if student:
        rows = fetch_all(
            "SELECT a.title, a.description, a.due_date, co.name AS course_name FROM assignments a "
            "JOIN courses co ON co.id=a.course_id "
            "JOIN enrollments e ON e.course_id=a.course_id "
            "WHERE e.student_id=? ORDER BY a.due_date", (student["id"],))
    return render_list(NAV, "assignments", "My Assignments", ASSIGNMENT_COLUMNS, rows,
                        allow_add=False, allow_edit=False, allow_delete=False)
