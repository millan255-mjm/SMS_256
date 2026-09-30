# EduManage Pro — Web Edition (Flask)

A browser-based rebuild of the Student Management System, with the same
role hierarchy — **Super Admin**, **Admin**, **Lecturer**, **Student** —
built to deploy on **Railway** so you can open it from a link on your phone.

## Files

| File / folder            | Purpose                                                              |
|---------------------------|-----------------------------------------------------------------------|
| `app.py`                  | Main Flask app — entry point Railway runs                            |
| `database.py`              | SQLite schema + all data-access functions                            |
| `helpers.py`               | Login/role decorators + generic list/form render helpers             |
| `auth.py`                  | Login / logout routes                                                |
| `superadmin.py`            | Super Admin routes (Admins, Users, Settings, Backup, Reports, Security) |
| `admin.py`                 | Admin routes (Students, Lecturers, Courses, Classes, Enrollment, Attendance, Reports) |
| `lecturer.py`              | Lecturer routes (Courses, Students, Attendance, Marks, Assignments, Performance) |
| `student.py`               | Student routes (Profile, Courses, Results, Attendance, Assignments)  |
| `report_utils.py`          | Shared stat calculations used by both Reports pages                  |
| `templates/`               | HTML pages (Jinja2)                                                   |
| `static/style.css`         | Dark theme styling                                                    |
| `requirements.txt`         | Python dependencies                                                   |
| `Procfile`                 | Tells Railway how to start the app (`gunicorn app:app`)               |
| `runtime.txt`               | Pins the Python version                                                |

## Deploying to Railway

**Option A — from GitHub (recommended)**
1. Push this folder to a new GitHub repository.
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → select your repo.
3. Railway auto-detects Python, installs `requirements.txt`, and runs the `Procfile` command.
4. Once deployed, open **Settings → Networking** and click **Generate Domain** — that gives you a public
   `https://your-app.up.railway.app` link you can open on your phone.

**Option B — Railway CLI**
```bash
npm install -g @railway/cli
railway login
cd sms_web
railway init
railway up
railway domain     # generates/shows your public URL
```

### Environment variables (set in Railway → Variables)
| Variable        | Required | Notes                                                                 |
|------------------|----------|------------------------------------------------------------------------|
| `SECRET_KEY`      | Yes (production) | Any long random string — used to sign login sessions               |
| `DATABASE_PATH`   | Recommended | Path to the SQLite file — see the persistence note below            |

### Important: database persistence
Railway's filesystem is **ephemeral** — without a volume, `sms_data.db` is wiped
on every redeploy/restart. To keep your data:
1. In Railway, add a **Volume** to your service (e.g. mount path `/data`).
2. Set the `DATABASE_PATH` variable to `/data/sms_data.db`.
3. Redeploy — the database now persists across deploys.

(For a small/demo setup you can skip the volume, just know the data resets on each deploy.)

## Running locally first (optional but recommended)
```bash
pip install -r requirements.txt
python app.py
```
Then open `http://localhost:5000` in your browser. A `sms_data.db` file is created automatically.

## Default login
```
Username: superadmin
Password: Admin@123
```
Change it from **Security & Permissions** after your first login.

## Typical workflow
1. Log in as **superadmin** → create an **Admin** account under *Manage Admins*.
2. Log out, log in as that Admin → add **Classes**, **Lecturers**, **Courses**, **Students**.
3. Use *Manage Enrollment* to enroll students into courses.
4. Log in as a **Lecturer** → record attendance, enter marks, post assignments.
5. Log in as a **Student** → view profile, courses, results, attendance, assignments — all from your phone browser.

## Testing note
Every route was exercised with Flask's test client (all 4 roles, every nav item,
full add/edit/delete flows, attendance recording, marks entry, and a password
change) and the app was also started with the exact production command
(`gunicorn app:app`) and hit with real HTTP requests before delivery.
