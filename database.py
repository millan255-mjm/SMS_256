"""
database.py — SQLite schema, connection helpers, and all data-access
functions for the EduManage Pro web app.
"""

import sqlite3
import hashlib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "sms_data.db"))


# ---------------------------------------------------------------------------
# Core connection helpers
# ---------------------------------------------------------------------------
def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def fetch_all(query, params=()):
    conn = get_conn()
    rows = [dict(r) for r in conn.execute(query, params).fetchall()]
    conn.close()
    return rows


def fetch_one(query, params=()):
    conn = get_conn()
    r = conn.execute(query, params).fetchone()
    conn.close()
    return dict(r) if r else None


def execute(query, params=()):
    conn = get_conn()
    cur = conn.execute(query, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def hash_pw(pw):
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def to_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT,
            year TEXT
        );

        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            student_no TEXT UNIQUE,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            class_id INTEGER,
            dob TEXT,
            gender TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(class_id) REFERENCES classes(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS lecturers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            staff_no TEXT UNIQUE,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            department TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT,
            credits INTEGER,
            department TEXT,
            lecturer_id INTEGER,
            FOREIGN KEY(lecturer_id) REFERENCES lecturers(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_id INTEGER,
            semester TEXT,
            enrolled_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_id INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            title TEXT,
            description TEXT,
            due_date TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_id INTEGER,
            exam_type TEXT,
            score REAL,
            max_score REAL,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    conn.commit()

    row = c.execute("SELECT id FROM users WHERE role='superadmin'").fetchone()
    if not row:
        c.execute(
            "INSERT INTO users(username,password,role,full_name,email,status) VALUES (?,?,?,?,?,?)",
            ("superadmin", hash_pw("Admin@123"), "superadmin", "System Administrator",
             "superadmin@edumanage.local", "active"),
        )
    defaults = {
        "institution_name": "EduManage Institute",
        "academic_year": "2026/2027",
        "contact_email": "info@edumanage.local",
    }
    for k, v in defaults.items():
        if not c.execute("SELECT key FROM settings WHERE key=?", (k,)).fetchone():
            c.execute("INSERT INTO settings(key,value) VALUES (?,?)", (k, v))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Admins (managed by Super Admin)
# ---------------------------------------------------------------------------
def fetch_admins():
    return fetch_all("SELECT * FROM users WHERE role='admin' ORDER BY id DESC")


def admin_fields():
    return [
        {"key": "username", "label": "Username", "type": "text"},
        {"key": "full_name", "label": "Full Name", "type": "text"},
        {"key": "email", "label": "Email", "type": "text"},
        {"key": "password", "label": "Password", "type": "password",
         "hint": "Leave blank to keep existing password when editing"},
    ]


def insert_admin(data):
    if not data.get("username") or not data.get("password"):
        raise ValueError("Username and password are required.")
    execute("INSERT INTO users(username,password,role,full_name,email,status) VALUES (?,?,?,?,?,?)",
            (data["username"], hash_pw(data["password"]), "admin", data.get("full_name", ""),
             data.get("email", ""), "active"))


def update_admin(rid, data):
    if data.get("password"):
        execute("UPDATE users SET username=?, full_name=?, email=?, password=? WHERE id=?",
                (data["username"], data.get("full_name", ""), data.get("email", ""),
                 hash_pw(data["password"]), rid))
    else:
        execute("UPDATE users SET username=?, full_name=?, email=? WHERE id=?",
                (data["username"], data.get("full_name", ""), data.get("email", ""), rid))


def delete_admin(rid):
    execute("DELETE FROM users WHERE id=?", (rid,))


# ---------------------------------------------------------------------------
# All Users (Super Admin, cross-role view)
# ---------------------------------------------------------------------------
def fetch_all_users():
    return fetch_all("SELECT * FROM users ORDER BY role, id DESC")


def all_users_fields():
    return [
        {"key": "username", "label": "Username", "type": "text"},
        {"key": "full_name", "label": "Full Name", "type": "text"},
        {"key": "email", "label": "Email", "type": "text"},
        {"key": "role", "label": "Role", "type": "select",
         "options": [{"value": r, "label": r} for r in ["superadmin", "admin", "lecturer", "student"]]},
        {"key": "status", "label": "Status", "type": "select",
         "options": [{"value": s, "label": s} for s in ["active", "suspended"]]},
        {"key": "password", "label": "New Password", "type": "password",
         "hint": "Leave blank to keep existing password"},
    ]


def update_user_any(rid, data):
    if data.get("password"):
        execute("UPDATE users SET username=?, full_name=?, email=?, role=?, status=?, password=? WHERE id=?",
                (data["username"], data.get("full_name", ""), data.get("email", ""), data["role"],
                 data["status"], hash_pw(data["password"]), rid))
    else:
        execute("UPDATE users SET username=?, full_name=?, email=?, role=?, status=? WHERE id=?",
                (data["username"], data.get("full_name", ""), data.get("email", ""), data["role"],
                 data["status"], rid))


def delete_user_any(rid):
    execute("DELETE FROM users WHERE id=?", (rid,))


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------
def fetch_classes():
    return fetch_all("SELECT * FROM classes ORDER BY id DESC")


def class_fields():
    return [
        {"key": "name", "label": "Class Name", "type": "text"},
        {"key": "department", "label": "Department", "type": "text"},
        {"key": "year", "label": "Year/Level", "type": "text"},
    ]


def insert_class(data):
    execute("INSERT INTO classes(name,department,year) VALUES (?,?,?)",
            (data.get("name", ""), data.get("department", ""), data.get("year", "")))


def update_class(rid, data):
    execute("UPDATE classes SET name=?, department=?, year=? WHERE id=?",
            (data.get("name", ""), data.get("department", ""), data.get("year", ""), rid))


def delete_class(rid):
    execute("DELETE FROM classes WHERE id=?", (rid,))


# ---------------------------------------------------------------------------
# Lecturers
# ---------------------------------------------------------------------------
def fetch_lecturers():
    return fetch_all(
        "SELECT l.*, u.username, u.status FROM lecturers l "
        "LEFT JOIN users u ON u.id = l.user_id ORDER BY l.id DESC"
    )


def lecturer_fields():
    return [
        {"key": "staff_no", "label": "Staff No.", "type": "text"},
        {"key": "full_name", "label": "Full Name", "type": "text"},
        {"key": "department", "label": "Department", "type": "text"},
        {"key": "email", "label": "Email", "type": "text"},
        {"key": "phone", "label": "Phone", "type": "text"},
        {"key": "username", "label": "Login Username", "type": "text"},
        {"key": "password", "label": "Password", "type": "password",
         "hint": "Leave blank to keep existing password when editing"},
    ]


def insert_lecturer(data):
    if not data.get("username") or not data.get("password"):
        raise ValueError("Username and password are required.")
    uid = execute("INSERT INTO users(username,password,role,full_name,email,status) VALUES (?,?,?,?,?,?)",
                   (data["username"], hash_pw(data["password"]), "lecturer", data.get("full_name", ""),
                    data.get("email", ""), "active"))
    execute("INSERT INTO lecturers(user_id,staff_no,full_name,email,phone,department) VALUES (?,?,?,?,?,?)",
            (uid, data.get("staff_no", ""), data.get("full_name", ""), data.get("email", ""),
             data.get("phone", ""), data.get("department", "")))


def update_lecturer(rid, data):
    row = fetch_one("SELECT * FROM lecturers WHERE id=?", (rid,))
    execute("UPDATE lecturers SET staff_no=?, full_name=?, email=?, phone=?, department=? WHERE id=?",
            (data.get("staff_no", ""), data.get("full_name", ""), data.get("email", ""),
             data.get("phone", ""), data.get("department", ""), rid))
    if row and row["user_id"]:
        if data.get("password"):
            execute("UPDATE users SET username=?, full_name=?, email=?, password=? WHERE id=?",
                    (data["username"], data.get("full_name", ""), data.get("email", ""),
                     hash_pw(data["password"]), row["user_id"]))
        else:
            execute("UPDATE users SET username=?, full_name=?, email=? WHERE id=?",
                    (data["username"], data.get("full_name", ""), data.get("email", ""), row["user_id"]))


def delete_lecturer(rid):
    row = fetch_one("SELECT * FROM lecturers WHERE id=?", (rid,))
    execute("DELETE FROM lecturers WHERE id=?", (rid,))
    if row and row["user_id"]:
        execute("DELETE FROM users WHERE id=?", (row["user_id"],))


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------
def fetch_students():
    return fetch_all(
        "SELECT s.*, c.name AS class_name, u.username, u.status FROM students s "
        "LEFT JOIN classes c ON c.id = s.class_id "
        "LEFT JOIN users u ON u.id = s.user_id ORDER BY s.id DESC"
    )


def student_fields():
    classes = fetch_classes()
    return [
        {"key": "student_no", "label": "Student No.", "type": "text"},
        {"key": "full_name", "label": "Full Name", "type": "text"},
        {"key": "class_id", "label": "Class", "type": "select",
         "options": [{"value": c["id"], "label": c["name"]} for c in classes]},
        {"key": "email", "label": "Email", "type": "text"},
        {"key": "phone", "label": "Phone", "type": "text"},
        {"key": "gender", "label": "Gender", "type": "select",
         "options": [{"value": g, "label": g} for g in ["Male", "Female", "Other"]]},
        {"key": "dob", "label": "Date of Birth", "type": "date"},
        {"key": "username", "label": "Login Username", "type": "text"},
        {"key": "password", "label": "Password", "type": "password",
         "hint": "Leave blank to keep existing password when editing"},
    ]


def insert_student(data):
    if not data.get("username") or not data.get("password"):
        raise ValueError("Username and password are required.")
    uid = execute("INSERT INTO users(username,password,role,full_name,email,status) VALUES (?,?,?,?,?,?)",
                   (data["username"], hash_pw(data["password"]), "student", data.get("full_name", ""),
                    data.get("email", ""), "active"))
    execute(
        "INSERT INTO students(user_id,student_no,full_name,email,phone,class_id,dob,gender) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (uid, data.get("student_no", ""), data.get("full_name", ""), data.get("email", ""),
         data.get("phone", ""), to_int(data.get("class_id")), data.get("dob", ""), data.get("gender", "")),
    )


def update_student(rid, data):
    row = fetch_one("SELECT * FROM students WHERE id=?", (rid,))
    execute(
        "UPDATE students SET student_no=?, full_name=?, email=?, phone=?, class_id=?, dob=?, gender=? WHERE id=?",
        (data.get("student_no", ""), data.get("full_name", ""), data.get("email", ""),
         data.get("phone", ""), to_int(data.get("class_id")), data.get("dob", ""),
         data.get("gender", ""), rid),
    )
    if row and row["user_id"]:
        if data.get("password"):
            execute("UPDATE users SET username=?, full_name=?, email=?, password=? WHERE id=?",
                    (data["username"], data.get("full_name", ""), data.get("email", ""),
                     hash_pw(data["password"]), row["user_id"]))
        else:
            execute("UPDATE users SET username=?, full_name=?, email=? WHERE id=?",
                    (data["username"], data.get("full_name", ""), data.get("email", ""), row["user_id"]))


def delete_student(rid):
    row = fetch_one("SELECT * FROM students WHERE id=?", (rid,))
    execute("DELETE FROM students WHERE id=?", (rid,))
    if row and row["user_id"]:
        execute("DELETE FROM users WHERE id=?", (row["user_id"],))


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------
def fetch_courses():
    return fetch_all(
        "SELECT co.*, l.full_name AS lecturer_name FROM courses co "
        "LEFT JOIN lecturers l ON l.id = co.lecturer_id ORDER BY co.id DESC"
    )


def course_fields():
    lecturers = fetch_lecturers()
    return [
        {"key": "code", "label": "Course Code", "type": "text"},
        {"key": "name", "label": "Course Name", "type": "text"},
        {"key": "credits", "label": "Credits", "type": "text"},
        {"key": "department", "label": "Department", "type": "text"},
        {"key": "lecturer_id", "label": "Lecturer", "type": "select",
         "options": [{"value": l["id"], "label": l["full_name"]} for l in lecturers]},
    ]


def insert_course(data):
    execute("INSERT INTO courses(code,name,credits,department,lecturer_id) VALUES (?,?,?,?,?)",
            (data.get("code", ""), data.get("name", ""), to_int(data.get("credits"), 0),
             data.get("department", ""), to_int(data.get("lecturer_id"))))


def update_course(rid, data):
    execute("UPDATE courses SET code=?, name=?, credits=?, department=?, lecturer_id=? WHERE id=?",
            (data.get("code", ""), data.get("name", ""), to_int(data.get("credits"), 0),
             data.get("department", ""), to_int(data.get("lecturer_id")), rid))


def delete_course(rid):
    execute("DELETE FROM courses WHERE id=?", (rid,))


# ---------------------------------------------------------------------------
# Enrollments
# ---------------------------------------------------------------------------
def fetch_enrollments():
    return fetch_all(
        "SELECT e.*, s.full_name AS student_name, s.student_no, co.name AS course_name, co.code "
        "FROM enrollments e "
        "JOIN students s ON s.id = e.student_id "
        "JOIN courses co ON co.id = e.course_id ORDER BY e.id DESC"
    )


def enrollment_fields():
    students = fetch_students()
    courses = fetch_courses()
    return [
        {"key": "student_id", "label": "Student", "type": "select",
         "options": [{"value": s["id"], "label": f"{s['student_no']} - {s['full_name']}"} for s in students]},
        {"key": "course_id", "label": "Course", "type": "select",
         "options": [{"value": c["id"], "label": f"{c['code']} - {c['name']}"} for c in courses]},
        {"key": "semester", "label": "Semester", "type": "text", "hint": "e.g. 2026 Semester 1"},
    ]


def insert_enrollment(data):
    sid, cid = to_int(data.get("student_id")), to_int(data.get("course_id"))
    if not sid or not cid:
        raise ValueError("Please select both a student and a course.")
    existing = fetch_one("SELECT id FROM enrollments WHERE student_id=? AND course_id=?", (sid, cid))
    if existing:
        raise ValueError("This student is already enrolled in that course.")
    execute("INSERT INTO enrollments(student_id,course_id,semester) VALUES (?,?,?)",
            (sid, cid, data.get("semester", "")))


def delete_enrollment(rid):
    execute("DELETE FROM enrollments WHERE id=?", (rid,))


# ---------------------------------------------------------------------------
# Attendance (admin read-only view)
# ---------------------------------------------------------------------------
def fetch_all_attendance():
    return fetch_all(
        "SELECT a.*, s.full_name AS student_name, s.student_no, co.name AS course_name "
        "FROM attendance a "
        "JOIN students s ON s.id = a.student_id "
        "JOIN courses co ON co.id = a.course_id "
        "ORDER BY a.date DESC"
    )


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
def get_setting(key, default=""):
    row = fetch_one("SELECT value FROM settings WHERE key=?", (key,))
    return row["value"] if row else default


def set_setting(key, value):
    if fetch_one("SELECT key FROM settings WHERE key=?", (key,)):
        execute("UPDATE settings SET value=? WHERE key=?", (value, key))
    else:
        execute("INSERT INTO settings(key,value) VALUES (?,?)", (key, value))


# ---------------------------------------------------------------------------
# Lecturer / Student record lookups (by linked user id)
# ---------------------------------------------------------------------------
def get_lecturer_record(user_id):
    return fetch_one("SELECT * FROM lecturers WHERE user_id=?", (user_id,))


def get_student_record(user_id):
    return fetch_one("SELECT * FROM students WHERE user_id=?", (user_id,))
