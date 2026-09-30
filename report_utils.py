"""
report_utils.py — Shared stat computation for the Reports page,
used by both the Super Admin and Admin dashboards.
"""

from database import fetch_one


def build_reports_context(nav_items, active):
    counts = [
        ("Students", fetch_one("SELECT COUNT(*) c FROM students")["c"], "#4f8cff"),
        ("Lecturers", fetch_one("SELECT COUNT(*) c FROM lecturers")["c"], "#2fbf80"),
        ("Courses", fetch_one("SELECT COUNT(*) c FROM courses")["c"], "#ffb648"),
        ("Classes", fetch_one("SELECT COUNT(*) c FROM classes")["c"], "#c77dff"),
        ("Enrollments", fetch_one("SELECT COUNT(*) c FROM enrollments")["c"], "#ff5c6c"),
        ("Admins", fetch_one("SELECT COUNT(*) c FROM users WHERE role='admin'")["c"], "#38c6f4"),
    ]
    total_att = fetch_one("SELECT COUNT(*) c FROM attendance")["c"]
    present_att = fetch_one("SELECT COUNT(*) c FROM attendance WHERE status='Present'")["c"]
    rate = round((present_att / total_att) * 100, 1) if total_att else 0.0
    return {
        "nav_items": nav_items, "active": active, "page_title": "Reports Overview",
        "stats": counts, "attendance_rate": rate, "present_count": present_att, "total_count": total_att,
    }
