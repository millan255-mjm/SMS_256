"""
admin.py — Admin routes: Manage Students, Manage Lecturers, Manage
Courses, Manage Classes, Manage Enrollment, Academic/Attendance, Reports.
"""

from flask import Blueprint, request, redirect, url_for, flash

from database import (
    fetch_students, student_fields, insert_student, update_student, delete_student,
    fetch_lecturers, lecturer_fields, insert_lecturer, update_lecturer, delete_lecturer,
    fetch_courses, course_fields, insert_course, update_course, delete_course,
    fetch_classes, class_fields, insert_class, update_class, delete_class,
    fetch_enrollments, enrollment_fields, insert_enrollment, delete_enrollment,
    fetch_all_attendance, fetch_one,
)
from helpers import role_required, render_list, render_form, render_template
from report_utils import build_reports_context

admin_bp = Blueprint("admin", __name__)

NAV = [
    {"endpoint": "admin.students_list", "icon": "\U0001F393", "label": "Manage Students", "key": "students"},
    {"endpoint": "admin.lecturers_list", "icon": "\U0001F468", "label": "Manage Lecturers", "key": "lecturers"},
    {"endpoint": "admin.courses_list", "icon": "\U0001F4DA", "label": "Manage Courses", "key": "courses"},
    {"endpoint": "admin.classes_list", "icon": "\U0001F3EB", "label": "Manage Classes", "key": "classes"},
    {"endpoint": "admin.enrollment_list", "icon": "\U0001F4DD", "label": "Manage Enrollment", "key": "enrollment"},
    {"endpoint": "admin.attendance_list", "icon": "\U0001F4C5", "label": "Academic/Attendance", "key": "attendance"},
    {"endpoint": "admin.reports", "icon": "\U0001F4CA", "label": "Reports", "key": "reports"},
]

STUDENT_COLUMNS = [("student_no", "Student No."), ("full_name", "Full Name"), ("class_name", "Class"),
                    ("email", "Email"), ("phone", "Phone"), ("status", "Status")]
LECTURER_COLUMNS = [("staff_no", "Staff No."), ("full_name", "Full Name"), ("department", "Department"),
                     ("email", "Email"), ("phone", "Phone")]
COURSE_COLUMNS = [("code", "Code"), ("name", "Course Name"), ("credits", "Credits"),
                   ("department", "Department"), ("lecturer_name", "Lecturer")]
CLASS_COLUMNS = [("name", "Class Name"), ("department", "Department"), ("year", "Year/Level")]
ENROLLMENT_COLUMNS = [("student_name", "Student"), ("student_no", "Student No."),
                       ("course_name", "Course"), ("code", "Code"), ("semester", "Semester")]
ATTENDANCE_COLUMNS = [("date", "Date"), ("student_name", "Student"), ("student_no", "Student No."),
                       ("course_name", "Course"), ("status", "Status")]


def _filtered(rows, q):
    if not q:
        return rows
    q = q.lower()
    return [r for r in rows if q in " ".join(str(v) for v in r.values()).lower()]


@admin_bp.route("/")
@role_required("admin")
def dashboard():
    return redirect(url_for("admin.students_list"))


# --- Manage Students ---
@admin_bp.route("/students")
@role_required("admin")
def students_list():
    q = request.args.get("q", "").strip()
    return render_list(NAV, "students", "Manage Students", STUDENT_COLUMNS, _filtered(fetch_students(), q),
                        add_endpoint="admin.students_add", edit_endpoint="admin.students_edit",
                        delete_endpoint="admin.students_delete", search=q)


@admin_bp.route("/students/add", methods=["GET", "POST"])
@role_required("admin")
def students_add():
    if request.method == "POST":
        try:
            insert_student(request.form)
            flash("Student added successfully.", "success")
            return redirect(url_for("admin.students_list"))
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
    return render_form(NAV, "students", "Add Student", student_fields(), back_endpoint="admin.students_list")


@admin_bp.route("/students/edit/<int:id>", methods=["GET", "POST"])
@role_required("admin")
def students_edit(id):
    row = fetch_one("SELECT * FROM students WHERE id=?", (id,))
    if not row:
        flash("Student not found.", "error")
        return redirect(url_for("admin.students_list"))
    if request.method == "POST":
        try:
            update_student(id, request.form)
            flash("Student updated successfully.", "success")
            return redirect(url_for("admin.students_list"))
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
    return render_form(NAV, "students", "Edit Student", student_fields(), initial=row,
                        back_endpoint="admin.students_list")


@admin_bp.route("/students/delete/<int:id>", methods=["POST"])
@role_required("admin")
def students_delete(id):
    delete_student(id)
    flash("Student deleted.", "success")
    return redirect(url_for("admin.students_list"))


# --- Manage Lecturers ---
@admin_bp.route("/lecturers")
@role_required("admin")
def lecturers_list():
    q = request.args.get("q", "").strip()
    return render_list(NAV, "lecturers", "Manage Lecturers", LECTURER_COLUMNS, _filtered(fetch_lecturers(), q),
                        add_endpoint="admin.lecturers_add", edit_endpoint="admin.lecturers_edit",
                        delete_endpoint="admin.lecturers_delete", search=q)


@admin_bp.route("/lecturers/add", methods=["GET", "POST"])
@role_required("admin")
def lecturers_add():
    if request.method == "POST":
        try:
            insert_lecturer(request.form)
            flash("Lecturer added successfully.", "success")
            return redirect(url_for("admin.lecturers_list"))
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
    return render_form(NAV, "lecturers", "Add Lecturer", lecturer_fields(), back_endpoint="admin.lecturers_list")


@admin_bp.route("/lecturers/edit/<int:id>", methods=["GET", "POST"])
@role_required("admin")
def lecturers_edit(id):
    row = fetch_one("SELECT * FROM lecturers WHERE id=?", (id,))
    if not row:
        flash("Lecturer not found.", "error")
        return redirect(url_for("admin.lecturers_list"))
    if request.method == "POST":
        try:
            update_lecturer(id, request.form)
            flash("Lecturer updated successfully.", "success")
            return redirect(url_for("admin.lecturers_list"))
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
    return render_form(NAV, "lecturers", "Edit Lecturer", lecturer_fields(), initial=row,
                        back_endpoint="admin.lecturers_list")


@admin_bp.route("/lecturers/delete/<int:id>", methods=["POST"])
@role_required("admin")
def lecturers_delete(id):
    delete_lecturer(id)
    flash("Lecturer deleted.", "success")
    return redirect(url_for("admin.lecturers_list"))


# --- Manage Courses ---
@admin_bp.route("/courses")
@role_required("admin")
def courses_list():
    q = request.args.get("q", "").strip()
    return render_list(NAV, "courses", "Manage Courses", COURSE_COLUMNS, _filtered(fetch_courses(), q),
                        add_endpoint="admin.courses_add", edit_endpoint="admin.courses_edit",
                        delete_endpoint="admin.courses_delete", search=q)


@admin_bp.route("/courses/add", methods=["GET", "POST"])
@role_required("admin")
def courses_add():
    if request.method == "POST":
        try:
            insert_course(request.form)
            flash("Course added successfully.", "success")
            return redirect(url_for("admin.courses_list"))
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
    return render_form(NAV, "courses", "Add Course", course_fields(), back_endpoint="admin.courses_list")


@admin_bp.route("/courses/edit/<int:id>", methods=["GET", "POST"])
@role_required("admin")
def courses_edit(id):
    row = fetch_one("SELECT * FROM courses WHERE id=?", (id,))
    if not row:
        flash("Course not found.", "error")
        return redirect(url_for("admin.courses_list"))
    if request.method == "POST":
        try:
            update_course(id, request.form)
            flash("Course updated successfully.", "success")
            return redirect(url_for("admin.courses_list"))
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
    return render_form(NAV, "courses", "Edit Course", course_fields(), initial=row,
                        back_endpoint="admin.courses_list")


@admin_bp.route("/courses/delete/<int:id>", methods=["POST"])
@role_required("admin")
def courses_delete(id):
    delete_course(id)
    flash("Course deleted.", "success")
    return redirect(url_for("admin.courses_list"))


# --- Manage Classes ---
@admin_bp.route("/classes")
@role_required("admin")
def classes_list():
    q = request.args.get("q", "").strip()
    return render_list(NAV, "classes", "Manage Classes", CLASS_COLUMNS, _filtered(fetch_classes(), q),
                        add_endpoint="admin.classes_add", edit_endpoint="admin.classes_edit",
                        delete_endpoint="admin.classes_delete", search=q)


@admin_bp.route("/classes/add", methods=["GET", "POST"])
@role_required("admin")
def classes_add():
    if request.method == "POST":
        try:
            insert_class(request.form)
            flash("Class added successfully.", "success")
            return redirect(url_for("admin.classes_list"))
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
    return render_form(NAV, "classes", "Add Class", class_fields(), back_endpoint="admin.classes_list")


@admin_bp.route("/classes/edit/<int:id>", methods=["GET", "POST"])
@role_required("admin")
def classes_edit(id):
    row = fetch_one("SELECT * FROM classes WHERE id=?", (id,))
    if not row:
        flash("Class not found.", "error")
        return redirect(url_for("admin.classes_list"))
    if request.method == "POST":
        try:
            update_class(id, request.form)
            flash("Class updated successfully.", "success")
            return redirect(url_for("admin.classes_list"))
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
    return render_form(NAV, "classes", "Edit Class", class_fields(), initial=row,
                        back_endpoint="admin.classes_list")


@admin_bp.route("/classes/delete/<int:id>", methods=["POST"])
@role_required("admin")
def classes_delete(id):
    delete_class(id)
    flash("Class deleted.", "success")
    return redirect(url_for("admin.classes_list"))


# --- Manage Enrollment ---
@admin_bp.route("/enrollment")
@role_required("admin")
def enrollment_list():
    q = request.args.get("q", "").strip()
    return render_list(NAV, "enrollment", "Manage Enrollment", ENROLLMENT_COLUMNS,
                        _filtered(fetch_enrollments(), q),
                        add_endpoint="admin.enrollment_add", delete_endpoint="admin.enrollment_delete",
                        allow_edit=False, search=q)


@admin_bp.route("/enrollment/add", methods=["GET", "POST"])
@role_required("admin")
def enrollment_add():
    if request.method == "POST":
        try:
            insert_enrollment(request.form)
            flash("Student enrolled successfully.", "success")
            return redirect(url_for("admin.enrollment_list"))
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
    return render_form(NAV, "enrollment", "Add Enrollment", enrollment_fields(),
                        back_endpoint="admin.enrollment_list")


@admin_bp.route("/enrollment/delete/<int:id>", methods=["POST"])
@role_required("admin")
def enrollment_delete(id):
    delete_enrollment(id)
    flash("Enrollment removed.", "success")
    return redirect(url_for("admin.enrollment_list"))


# --- Academic / Attendance (read-only) ---
@admin_bp.route("/attendance")
@role_required("admin")
def attendance_list():
    q = request.args.get("q", "").strip()
    return render_list(NAV, "attendance", "Academic / Attendance Records", ATTENDANCE_COLUMNS,
                        _filtered(fetch_all_attendance(), q),
                        allow_add=False, allow_edit=False, allow_delete=False, search=q)


# --- Reports ---
@admin_bp.route("/reports")
@role_required("admin")
def reports():
    return render_template("reports.html", **build_reports_context(NAV, "reports"))
