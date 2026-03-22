# Daily Dose

Flask web app for medication scheduling: dependents manage their own plan; carers can link to dependents, view or edit their schedules, and see adherence reports.

## Tech stack

- **Flask** — Web framework
- **Flask-SQLAlchemy** — ORM (default SQLite: `instance/app.db`)
- **Flask-Login** — Sessions and `@login_required`
- **Flask-WTF / WTForms** — Forms and CSRF
- **pytest** — Tests (in-memory SQLite via `tests/conftest.py`, separate from dev DB)

## Project layout

```
app/
├── __init__.py        # App factory wiring, blueprints, db.create_all()
├── config.py          # Config (SECRET_KEY, DATABASE_URI, etc.)
├── forms/             # WTForms (auth, schedule)
├── models/
│   ├── schedule.py    # Schedule, Prescription, Medication, MedicationLog
│   └── users.py       # User, carer–dependent association table
├── routes/
│   ├── main.py        # `/` entry (redirects by auth and role)
│   ├── auth.py        # Login, register, logout
│   ├── schedule.py    # Dependent medication plan (prefix `/schedule`)
│   └── carer.py       # Carer dependents & reports (prefix `/carer`)
├── services/          # User, schedule, carer/dependent logic
├── templates/         # Jinja templates (auth, schedule, carer; see note below)
└── static/            # CSS, etc.
tests/                 # pytest (e.g. test_auth, test_schedule_service, test_main)
```

## Main URLs

| Path | Purpose |
|------|--------|
| **`GET /`** | Not logged in → **302** to `/login`. Logged-in **carer** → `/carer/dependents`. Logged-in **dependent** → `/schedule` (plan). |
| **`/login`**, **`/register`**, **`POST /logout`** | Authentication (Flask-Login). |
| **`/schedule/*`** | Dependent-only medication plan (prescriptions, medications, “taken” logging). |
| **`/carer/*`** | Carer-only: dependents list, add/remove, manage dependent schedules, weekly adherence report. |

## Run and test

1. **Install:** `pip install -r requirements.txt`
2. **Configure:** optional `.env` or env vars (see `app/config.py`), e.g. `SECRET_KEY`, `DATABASE_URI`.
3. **Run:** from project root, e.g. `flask --app app run` (or set `FLASK_APP=app` and run `flask run`).
4. **Tests:** `pytest` — uses in-memory SQLite so `instance/app.db` is not touched.

The dev database file is created when needed; tables are ensured at app startup with `db.create_all()`.
