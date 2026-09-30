"""
lecturer.py — Lecturer routes: My Courses, My Students, Record
Attendance, Enter Marks, Manage Assignments, Student Performance.
"""

import datetime

from flask import Blueprint, request, redirect, url_for, flash, session, abort

from database import (
    fetch_all, fetch_one, execute, to_int, get_lecturer_record,
)
from helpers import role_required, render_list, render_form, render_template

lecturer_bp = Blueprint("lecturer", __name__)

NAV = [
    {"endpoint": "lecturer.courses_list", "icon": "\U0001F4DA", "label": "My Courses", "key": "courses"},
    {"endpoint": "lecturer.students_list", "icon": "\U0001F393", "label": "My Students", "key": "students"},
    {"endpoint": "lecturer.attendance", "icon": "\U0001F4C5", "label": "Record Attendance", "key": "attendance"},
    {"endpoint": "lecturer.marks", "icon": "\U0001F4CB", "label": "Enter Marks", "key": "marks"},
    {"endpoint": "lecturer.assignments_list", "icon": "\U0001F4DD", "label": "Manage Assignments", "key": "assignments"},
    {"endpoint": "lecturer.performance", "icon": "\U0001F4C8", "label": "Student Performance", "key": "performance"},
]

COURSE_COLUMNS = [("code", "Code"), ("name", "Course Name"), ("credits", "Credits"), ("department", "Department")]
STUDENT_COLUMNS = [("student_no", "Student No."), ("full_name", "Full Name"), ("course_name", "Course"),
                    ("email", "Email"), ("phone", "Phone")]
ASSIGNMENT_COLUMNS = [("title", "Title"), ("course_name", "Course"), ("due_date", "Due Date")]
PERFORMANCE_COLUMNS = [("student_no", "Student No."), ("full_name", "Full Name"), ("course_name", "Course"),
                        ("exam_type", "Type"), ("score", "Score"), ("max_score", "Max")]


def _current_lecturer():
    return get_lecturer_record(session["user_id"])


def _my_courses(lecturer):
    if not lecturer:
        return []
    return fetch_all("SELECT * FROM courses WHERE lecturer_id=? ORDER BY id DESC", (lecturer["id"],))


def _require_lecturer():
    lecturer = _current_lecturer()
    if not lecturer:
        flash("No lecturer profile is linked to this account. Please contact an administrator.", "error")
    return lecturer


@lecturer_bp.route("/")
@role_required("lecturer")
def dashboard():
    return redirect(url_for("lecturer.courses_list"))


@lecturer_bp.route("/courses")
@role_required("lecturer")
def courses_list():
    lecturer = _require_lecturer()
    return render_list(NAV, "courses", "My Courses", COURSE_COLUMNS, _my_courses(lecturer),
                        allow_add=False, allow_edit=False, allow_delete=False)


@lecturer_bp.route("/students")
@role_required("lecturer")
def students_list():
    lecturer = _require_lecturer()
    course_ids = [c["id"] for c in _my_courses(lecturer)]
    rows = []
    if course_ids:
        placeholders = ",".join("?" * len(course_ids))
        rows = fetch_all(
            f"SELECT DISTINCT s.student_no, s.full_name, s.email, s.phone, co.name AS course_name "
            f"FROM enrollments e JOIN students s ON s.id=e.student_id "
            f"JOIN courses co ON co.id=e.course_id "
            f"WHERE e.course_id IN ({placeholders}) ORDER BY s.full_name", course_ids)
    return render_list(NAV, "students", "My Students", STUDENT_COLUMNS, rows,
                        allow_add=False, allow_edit=False, allow_delete=False)


def _own_course_or_404(lecturer, course_id):
    course = fetch_one("SELECT * FROM courses WHERE id=? AND lecturer_id=?", (course_id, lecturer["id"]))
    if not course:
        abort(404)
    return course


@lecturer_bp.route("/attendance", methods=["GET", "POST"])
@role_required("lecturer")
def attendance():
    lecturer = _require_lecturer()
    courses = _my_courses(lecturer)
    if not lecturer:
        return render_template("lecturer/attendance.html", nav_items=NAV, active="attendance",
                                page_title="Record Attendance", courses=[], course_id=None,
                                date=datetime.date.today().isoformat(), students=[], statuses={})

    if request.method == "POST":
        course_id = to_int(request.form.get("course_id"))
        date = request.form.get("date") or datetime.date.today().isoformat()
        course = _own_course_or_404(lecturer, course_id)
        students = fetch_all(
            "SELECT s.id FROM enrollments e JOIN students s ON s.id=e.student_id "
            "WHERE e.course_id=?", (course["id"],))
        for s in students:
            status = request.form.get(f"status_{s['id']}", "Present")
            existing = fetch_one(
                "SELECT id FROM attendance WHERE student_id=? AND course_id=? AND date=?",
                (s["id"], course["id"], date))
            if existing:
                execute("UPDATE attendance SET status=? WHERE id=?", (status, existing["id"]))
            else:
                execute("INSERT INTO attendance(student_id,course_id,date,status) VALUES (?,?,?,?)",
                        (s["id"], course["id"], date, status))
        flash("Attendance recorded successfully.", "success")
        return redirect(url_for("lecturer.attendance", course_id=course["id"], date=date))

    course_id = to_int(request.args.get("course_id"))
    date = request.args.get("date") or datetime.date.today().isoformat()
    students, statuses = [], {}
    if course_id:
        course = _own_course_or_404(lecturer, course_id)
        students = fetch_all(
            "SELECT s.id, s.student_no, s.full_name FROM enrollments e "
            "JOIN students s ON s.id=e.student_id WHERE e.course_id=? ORDER BY s.full_name", (course["id"],))
        existing_records = fetch_all(
            "SELECT student_id, status FROM attendance WHERE course_id=? AND date=?", (course["id"], date))
        statuses = {r["student_id"]: r["status"] for r in existing_records}

    return render_template("lecturer/attendance.html", nav_items=NAV, active="attendance",
                            page_title="Record Attendance", courses=courses, course_id=course_id,
                            date=date, students=students, statuses=statuses)


@lecturer_bp.route("/marks", methods=["GET", "POST"])
@role_required("lecturer")
def marks():
    lecturer = _require_lecturer()
    courses = _my_courses(lecturer)
    if not lecturer:
        return render_template("lecturer/marks.html", nav_items=NAV, active="marks",
                                page_title="Enter Marks", courses=[], course_id=None, students=[])

    if request.method == "POST":
        course_id = to_int(request.form.get("course_id"))
        course = _own_course_or_404(lecturer, course_id)
        exam_type = request.form.get("exam_type", "CA")
        try:
            max_score = float(request.form.get("max_score", "100") or 100)
        except ValueError:
            max_score = 100.0
        students = fetch_all(
            "SELECT s.id FROM enrollments e JOIN students s ON s.id=e.student_id "
            "WHERE e.course_id=?", (course["id"],))
        for s in students:
            raw = request.form.get(f"score_{s['id']}")
            try:
                score = float(raw)
            except (TypeError, ValueError):
                continue
            execute(
                "INSERT INTO marks(student_id,course_id,exam_type,score,max_score) VALUES (?,?,?,?,?)",
                (s["id"], course["id"], exam_type, score, max_score))
        flash("Marks recorded successfully.", "success")
        return redirect(url_for("lecturer.marks", course_id=course["id"]))

    course_id = to_int(request.args.get("course_id"))
    students = []
    if course_id:
        course = _own_course_or_404(lecturer, course_id)
        students = fetch_all(
            "SELECT s.id, s.student_no, s.full_name FROM enrollments e "
            "JOIN students s ON s.id=e.student_id WHERE e.course_id=? ORDER BY s.full_name", (course["id"],))

    return render_template("lecturer/marks.html", nav_items=NAV, active="marks",
                            page_title="Enter Marks", courses=courses, course_id=course_id, students=students)


@lecturer_bp.route("/assignments")
@role_required("lecturer")
def assignments_list():
    lecturer = _require_lecturer()
    course_ids = [c["id"] for c in _my_courses(lecturer)]
    rows = []
    if course_ids:
        placeholders = ",".join("?" * len(course_ids))
        rows = fetch_all(
            f"SELECT a.*, co.name AS course_name FROM assignments a "
            f"JOIN courses co ON co.id=a.course_id WHERE a.course_id IN ({placeholders}) "
            f"ORDER BY a.id DESC", course_ids)
    return render_list(NAV, "assignments", "Manage Assignments", ASSIGNMENT_COLUMNS, rows,
                        add_endpoint="lecturer.assignments_add", edit_endpoint="lecturer.assignments_edit",
                        delete_endpoint="lecturer.assignments_delete")


def _assignment_fields(lecturer):
    courses = _my_courses(lecturer)
    return [
        {"key": "title", "label": "Title", "type": "text"},
        {"key": "course_id", "label": "Course", "type": "select",
         "options": [{"value": c["id"], "label": f"{c['code']} - {c['name']}"} for c in courses]},
        {"key": "due_date", "label": "Due Date", "type": "date"},
        {"key": "description", "label": "Description", "type": "text"},
    ]


@lecturer_bp.route("/assignments/add", methods=["GET", "POST"])
@role_required("lecturer")
def assignments_add():
    lecturer = _require_lecturer()
    if not lecturer:
        return redirect(url_for("lecturer.assignments_list"))
    if request.method == "POST":
        course_id = to_int(request.form.get("course_id"))
        _own_course_or_404(lecturer, course_id)
        execute("INSERT INTO assignments(course_id,title,description,due_date) VALUES (?,?,?,?)",
                (course_id, request.form.get("title", ""), request.form.get("description", ""),
                 request.form.get("due_date", "")))
        flash("Assignment added successfully.", "success")
        return redirect(url_for("lecturer.assignments_list"))
    return render_form(NAV, "assignments", "Add Assignment", _assignment_fields(lecturer),
                        back_endpoint="lecturer.assignments_list")


@lecturer_bp.route("/assignments/edit/<int:id>", methods=["GET", "POST"])
@role_required("lecturer")
def assignments_edit(id):
    lecturer = _require_lecturer()
    if not lecturer:
        return redirect(url_for("lecturer.assignments_list"))
    row = fetch_one("SELECT * FROM assignments WHERE id=?", (id,))
    if not row:
        flash("Assignment not found.", "error")
        return redirect(url_for("lecturer.assignments_list"))
    _own_course_or_404(lecturer, row["course_id"])
    if request.method == "POST":
        course_id = to_int(request.form.get("course_id"))
        _own_course_or_404(lecturer, course_id)
        execute("UPDATE assignments SET course_id=?, title=?, description=?, due_date=? WHERE id=?",
                (course_id, request.form.get("title", ""), request.form.get("description", ""),
                 request.form.get("due_date", ""), id))
        flash("Assignment updated successfully.", "success")
        return redirect(url_for("lecturer.assignments_list"))
    return render_form(NAV, "assignments", "Edit Assignment", _assignment_fields(lecturer), initial=row,
                        back_endpoint="lecturer.assignments_list")


@lecturer_bp.route("/assignments/delete/<int:id>", methods=["POST"])
@role_required("lecturer")
def assignments_delete(id):
    lecturer = _require_lecturer()
    row = fetch_one("SELECT * FROM assignments WHERE id=?", (id,))
    if lecturer and row:
        _own_course_or_404(lecturer, row["course_id"])
        execute("DELETE FROM assignments WHERE id=?", (id,))
        flash("Assignment deleted.", "success")
    return redirect(url_for("lecturer.assignments_list"))


@lecturer_bp.route("/performance")
@role_required("lecturer")
def performance():
    lecturer = _require_lecturer()
    course_ids = [c["id"] for c in _my_courses(lecturer)]
    rows = []
    if course_ids:
        placeholders = ",".join("?" * len(course_ids))
        rows = fetch_all(
            f"SELECT s.student_no, s.full_name, co.name AS course_name, m.exam_type, m.score, m.max_score "
            f"FROM marks m JOIN students s ON s.id=m.student_id JOIN courses co ON co.id=m.course_id "
            f"WHERE m.course_id IN ({placeholders}) ORDER BY s.full_name", course_ids)
    return render_list(NAV, "performance", "Student Performance", PERFORMANCE_COLUMNS, rows,
                        allow_add=False, allow_edit=False, allow_delete=False)
